import redis
import random
from decimal import Decimal
from django.db import transaction
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

r = settings.REDIS_CLIENT

class GameService:
    @staticmethod
    def find_user_game(user):
        from games.models import GamePlayer
        gp = (
            GamePlayer.objects
            .filter(user=user, game__status__in=["waiting", "running"])
            .first()
        )
        return gp.game.id if gp else None

    @staticmethod
    def ensure_player_in_game(user, game_id):
        from games.models import Game, GamePlayer
        game = Game.objects.get(id=game_id)

        # Не добавляем игрока в завершённую игру
        if game.status == "finished":
            return

        if not GamePlayer.objects.filter(game=game, user=user).exists():
            GamePlayer.objects.create(
                game=game,
                user=user,
                bet_ton=Decimal("0.00")
            )

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

            if not GamePlayer.objects.filter(game=game, user=user).exists():
                GamePlayer.objects.create(
                    game=game,
                    user=user,
                    bet_ton=Decimal("0.00"),
                )

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

        game = Game.objects.prefetch_related("players").get(id=game_id)
        total_bet = sum([p.bet_ton for p in game.players.all()])

        # Считаем шансы
        for p in game.players.all():
            chance = (p.bet_ton / total_bet) * 100 if total_bet > 0 else 0
            GamePlayer.objects.filter(id=p.id).update(chance_percent=chance)

        game.pot_amount_ton = total_bet
        game.save()

        # === Проверка условий старта таймера ===
        # Считаем игроков, которые реально сделали ставку
        active_players_count = GamePlayer.objects.filter(
            game_id=game_id,
            bet_ton__gt=0
        ).count()

        if active_players_count >= 2 and game.status!="finished":
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
        game = Game.objects.prefetch_related("players__user").get(id=game_id)
        players_data = [
            {
                "id": p.user.id,
                "username": p.user.username,
                "bet_ton": str(p.bet_ton),
                "chance_percent": float(p.chance_percent),
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
        players = list(GamePlayer.objects.filter(game_id=game_id).select_related("user"))

        if not players:
            game.status = "finished"
            game.save(update_fields=["status"])
            return {"status": "finished", "winner": None}

        total_bet = sum(float(p.bet_ton) for p in players)

        # Определяем победителя
        if total_bet == 0:
            winner = random.choice(players)
        else:
            weights = [float(p.bet_ton) / total_bet for p in players]
            winner = random.choices(players, weights=weights, k=1)[0]

        # --- Финансовая логика ---
        from django.db import transaction
        with transaction.atomic():
            # списываем ставки у всех
            for p in players:
                if p.bet_ton > 0:
                    p.user.balance_ton -= p.bet_ton
                    p.user.save(update_fields=["balance_ton"])

            # начисляем победителю банк
            if total_bet > 0:
                winner.user.balance_ton += Decimal(str(total_bet))
                winner.user.save(update_fields=["balance_ton"])

            # обновляем игру
            game.status = "finished"
            game.save(update_fields=["status"])
            game.winner = p.user
            game.save(update_fields=["winner"])

        return {
            "status": "finished",
            "winner": winner.user.username,
            "pot": total_bet,
            "players": [
                {
                    "username": p.user.username,
                    "bet": float(p.bet_ton),
                    "chance": round((float(p.bet_ton) / total_bet) * 100, 2) if total_bet > 0 else 0,
                    "final_balance": float(p.user.balance_ton)
                }
                for p in players
            ]
        }