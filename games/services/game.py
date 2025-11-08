import redis
import random
import logging
from decimal import Decimal
from django.db import transaction
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

r = settings.REDIS_CLIENT
logger = logging.getLogger('games.services.game')

class GameService:
    @staticmethod
    def find_user_game(user):
        from games.models import GamePlayer
        gp = (
            GamePlayer.objects
            .filter(user=user, game__status__in=["waiting", "running"])
            .first()
        )
        if gp:
            logger.info(f"Найдена активная игра {gp.game.id} для пользователя {user.username}")
        else:
            logger.info(f"Активных игр не найдено для пользователя {user.username}")
        return gp.game.id if gp else None

    @staticmethod
    def ensure_player_in_game(user, game_id):
        from games.models import Game, GamePlayer
        game = Game.objects.get(id=game_id)

        # Не добавляем игрока в завершённую игру
        if game.status == "finished":
            logger.warning(f"Попытка добавить пользователя {user.username} в завершенную игру {game_id}")
            return

        if not GamePlayer.objects.filter(game=game, user=user).exists():
            GamePlayer.objects.create(
                game=game,
                user=user,
                bet_ton=Decimal("0.00")
            )
            logger.info(f"Пользователь {user.username} добавлен в игру {game_id}")
        else:
            logger.info(f"Пользователь {user.username} уже в игре {game_id}")

    @staticmethod
    def get_or_create_game_and_player(user):
        from games.models import Game, GamePlayer
        with transaction.atomic():
            game = (
                Game.objects
                .filter(status="waiting", mode="pvp")
                .select_for_update()
                .first()
            )
            if not game:
                game = Game.objects.create(mode="pvp", status="waiting")
                logger.info(f"Создана новая игра {game.id} для пользователя {user.username}")
            else:
                logger.info(f"Найдена ожидающая игра {game.id} для пользователя {user.username}")

            if not GamePlayer.objects.filter(game=game, user=user).exists():
                GamePlayer.objects.create(
                    game=game,
                    user=user,
                    bet_ton=Decimal("0.00"),
                )
                logger.info(f"Пользователь {user.username} добавлен в игру {game.id}")

        return game.id, f"pvp_{game.id}"

    @staticmethod
    def update_bet(user, amount, game_id):
        from games.models import GamePlayer

        # Приводим amount к Decimal
        amount = Decimal(amount)

        # Проверка баланса
        # if not settings.DEBUG:
        if user.balance_ton < amount:
            raise ValidationError(_("Недостаточно средств на балансе TON"))

        # Списываем деньги (можно atomic update)
        # user.balance_ton -= amount
        # user.save(update_fields=["balance_ton"])

        # Обновляем ставку в игре
        GamePlayer.objects.filter(game_id=game_id, user=user).update(bet_ton=amount)

    @staticmethod
    def calc_and_save_pot_chances(game_id):
        from games.models import Game, GamePlayer
        from games.tasks import start_timer_task, send_timer_task, finish_game_task

        game = Game.objects.prefetch_related("players__gifts").get(id=game_id)

        # Пересчитываем total_bet_ton для каждого игрока
        total_bet = Decimal("0.00")
        for p in game.players.all():
            p.recalc_total()
            p.save(update_fields=["total_bet_ton"])  # сохраняем пересчитанное значение
            total_bet += p.total_bet_ton

        # Считаем шансы
        for p in game.players.all():
            chance = (p.total_bet_ton / total_bet * 100) if total_bet > 0 else 0
            GamePlayer.objects.filter(id=p.id).update(chance_percent=chance)

        # Обновляем банк игры
        game.pot_amount_ton = total_bet
        game.save(update_fields=["pot_amount_ton"])

        # === Проверка условий старта таймера ===
        active_players_count = GamePlayer.objects.filter(
            game_id=game_id,
            total_bet_ton__gt=0
        ).count()

        if active_players_count >= 2 and game.status != "finished":
            timer_key = f"game_timer:{game_id}"
            if not r.exists(timer_key):
                r.set(timer_key, "running", ex=40)

                Game.objects.filter(id=game_id).update(status="running")

                # Сообщаем, что пошёл таймер
                start_timer_task.apply_async(args=[game_id, 40])

                # Запуск секундомера
                send_timer_task.apply_async(args=[game_id, 40])

                # Завершение игры
                finish_game_task.apply_async(args=[game_id], countdown=40)

    @staticmethod
    def get_game_state(game_id):
        from games.models import Game
        game = Game.objects.prefetch_related("players__user", "players__gifts").get(id=game_id)
        players_data = [
            {
                "id": p.user.id,
                "username": p.user.username,
                "avatar_url": p.user.get_avatar_url(),
                "bet_ton": str(p.bet_ton),
                "chance_percent": float(p.chance_percent),
                "gifts": [
                    {
                        "id": gift.id,
                        "user_username": gift.user.username,
                        "ton_contract_address": gift.ton_contract_address,
                        "name": gift.name,
                        "image_url": gift.image_url,
                        "price_ton": str(gift.price_ton),
                        "backdrop": gift.backdrop,
                        "symbol": gift.symbol,
                        "model_name": gift.model_name,
                        "pattern_name": gift.pattern_name,
                        "model_rarity_permille": gift.model_rarity_permille,
                        "pattern_rarity_permille": gift.pattern_rarity_permille,
                        "backdrop_rarity_permille": gift.backdrop_rarity_permille,
                        "model_original_details": gift.model_original_details,
                        "pattern_original_details": gift.pattern_original_details,
                        "backdrop_original_details": gift.backdrop_original_details,
                        "rarity_level": gift.rarity_level,
                        "backdrop": gift.backdrop,
                    }
                    for gift in p.gifts.all()
                ],
            }
            for p in game.players.all()
        ]
        return {
            "game_id": game.id,
            "status": game.status,
            "pot_amount_ton": str(game.pot_amount_ton),
            "players": players_data,
        }

    @staticmethod
    def add_player_to_game(game_id, user):
        from games.tasks import finish_game_task
        from games.models import Game, GamePlayer, Game as GameModel

        GamePlayer.objects.get_or_create(game_id=game_id, user=user)

        count = GamePlayer.objects.filter(game_id=game_id).count()

    @staticmethod
    def finish_game(game_id):
        from games.models import Game, GamePlayer

        game = Game.objects.get(id=game_id)
        players = list(
            GamePlayer.objects
            .filter(game_id=game_id)
            .select_related("user")
            .prefetch_related("gifts")
        )

        if not players:
            game.status = "finished"
            game.save(update_fields=["status"])
            return {"status": "finished", "winner": None}

        # Пересчитываем total для корректного розыгрыша (TON + подарки)
        for p in players:
            p.recalc_total()

        # Общая сумма ставок: эквивалент (TON + подарки) — для определения победителя
        total_equiv_decimal = sum((p.total_bet_ton for p in players), Decimal("0.00"))
        total_equiv = float(total_equiv_decimal)
        # Сумма TON ставок — для реального начисления баланса победителю
        total_ton_decimal = sum((p.bet_ton for p in players), Decimal("0.00"))

        # Определяем победителя
        if total_equiv == 0:
            winner = random.choice(players)
        else:
            # Используем итоговую ставку (TON + подарки) как вес
            weights = [float(p.total_bet_ton) / total_equiv for p in players]
            winner = random.choices(players, weights=weights, k=1)[0]

        # --- Финансовая логика ---
        from django.db import transaction
        with transaction.atomic():
            # списываем ставки у всех
            for p in players:
                if p.bet_ton > 0:
                    p.user.balance_ton -= p.bet_ton
                    p.user.save(update_fields=["balance_ton"])

            # передаём все поставленные подарки победителю
            for p in players:
                player_gifts = list(p.gifts.all())
                if not player_gifts:
                    continue
                for gift in player_gifts:
                    # меняем владельца подарка на победителя
                    gift.user = winner.user
                    gift.save(update_fields=["user"])
                # очищаем привязку подарков к ставке игрока в этой игре
                p.gifts.clear()

            # начисляем победителю банк (только TON)
            if total_ton_decimal > 0:
                winner.user.balance_ton += total_ton_decimal
                winner.user.save(update_fields=["balance_ton"])

            # обновляем игру
            game.status = "finished"
            # сохраняем финальный банк в игре как эквивалент (TON + gifts)
            game.pot_amount_ton = total_equiv_decimal
            game.winner = winner.user
            game.save(update_fields=["status", "pot_amount_ton", "winner"])

        return {
            "id": game.id,
            "hash": game.hash,
            "started_at": game.started_at.isoformat() if game.started_at else None,
            "ended_at": game.ended_at.isoformat() if game.ended_at else None,
            "winner": {
                "id": winner.user.id,
                "username": getattr(winner.user, "username", None),
                "avatar_url": winner.user.get_avatar_url(),
            },
            "winner_gifts": [
                {
                    "id": gift.id,
                    "ton_contract_address": gift.ton_contract_address,
                    "name": gift.name,
                    "image_url": gift.image_url,
                    "price_ton": str(gift.price_ton),
                    "backdrop": gift.backdrop,
                    "symbol": gift.symbol,
                }
                for gift in winner.gifts.all()
            ],
            "win_amount_ton": f"{(total_equiv_decimal * (1 - game.commission_percent / Decimal('100'))):.2f}",
            "winner_chance_percent": str(winner.chance_percent) if winner.chance_percent else "0",
        }
        