import redis
import random
from decimal import Decimal
from django.db import transaction
from asgiref.sync import sync_to_async
from django.conf import settings

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
        if user.balance_ton < amount:
            raise ValidationError(_("Недостаточно средств на балансе TON"))

        # Списываем деньги (можно atomic update)
        user.balance_ton -= amount
        user.save(update_fields=["balance_ton"])

        # Обновляем ставку в игре
        GamePlayer.objects.filter(game_id=game_id, user=user).update(bet_ton=amount)

    @staticmethod
    def calc_and_save_pot_chances(game_id):
        from games.models import Game, GamePlayer
        game = Game.objects.prefetch_related("players").get(id=game_id)
        total_bet = sum([p.bet_ton for p in game.players.all()])

        for p in game.players.all():
            chance = (p.bet_ton / total_bet) * 100 if total_bet > 0 else 0
            GamePlayer.objects.filter(id=p.id).update(chance_percent=chance)

        game.pot_amount_ton = total_bet
        game.save()

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

        if count >= 2:
            timer_key = f"game_timer:{game_id}"
            if not r.exists(timer_key):
                r.set(timer_key, "running", ex=40)

                # Обновляем статус игры на "running"
                GameModel.objects.filter(id=game_id).update(status="running")

                finish_game_task.apply_async(args=[game_id], countdown=40)


    @staticmethod
    def finish_game(game_id):
        from games.models import Game, GamePlayer
        game = Game.objects.get(id=game_id)
        players = list(GamePlayer.objects.filter(game_id=game_id))

        if not players:
            game.status = Game.Status.FINISHED
            game.save(update_fields=["status"])
            return {"status": "finished", "winner": None}

        # Выбор победителя (рандом)
        winner = random.choice(players)
        game.status = "finished"  # соответствующее значение из status_choices
        game.save(update_fields=["status"])

        return {
            "status": "finished",
            "winner": winner.user.username,
            "pot": float(sum(p.bet_ton for p in players)),
            "players": [
                {
                    "username": p.user.username,
                    "bet": float(p.bet_ton),
                    "chance": round(
                        (float(p.bet_ton) / float(sum(x.bet_ton for x in players))) * 100, 2
                    )
                }
                for p in players
            ]
        }
