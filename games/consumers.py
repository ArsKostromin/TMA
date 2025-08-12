import json
from decimal import Decimal
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class PvpGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Здесь не проверяем user, тк аутентификация по первому сообщению
        from django.contrib.auth.models import AnonymousUser

        self.scope["user"] = AnonymousUser()
        await self.accept()
        self.authenticated = False
        self.game_id = None
        self.room_group_name = None

    async def disconnect(self, close_code):
        if self.authenticated and self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if not self.authenticated:
            # Первое сообщение — authenticate с токеном
            if action == "authenticate":
                token = data.get("token")
                if not token:
                    await self.close()
                    return

                user = await self.get_user_from_token(token)
                if user is None or not user.is_authenticated:
                    await self.close()
                    return

                self.scope["user"] = user
                self.authenticated = True

                # Попытка найти игру, где есть этот игрок
                game_id = await sync_to_async(self.find_user_game)(user)

                if game_id:
                    self.game_id = game_id
                    self.room_group_name = f"pvp_{game_id}"
                    await sync_to_async(self.ensure_player_in_game)(user, game_id)
                else:
                    # Если игры нет, создаем новую и игрока в ней
                    game_id, room_group_name = await sync_to_async(self.get_or_create_game_and_player)(user)
                    self.game_id = game_id
                    self.room_group_name = room_group_name

                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                await self.send_game_state()
            else:
                # Если первое сообщение не authenticate — кикнем
                await self.close()
            return

        # Пользователь аутентифицирован, обрабатываем действия
        if action == "bet":
            amount = Decimal(data.get("amount", "0"))
            user = self.scope["user"]
            await sync_to_async(self.update_bet)(user, amount)
            await self.update_pot_and_chances()

    async def get_user_from_token(self, token):
        try:
            import jwt
            from django.conf import settings
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                return None

            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)
            return user
        except Exception:
            return None

    def find_user_game(self, user):
        from games.models import GamePlayer
        gp = GamePlayer.objects.filter(user=user).first()
        return gp.game.id if gp else None

    def ensure_player_in_game(self, user, game_id):
        from games.models import GamePlayer, Game
        from decimal import Decimal
        game = Game.objects.get(id=game_id)
        if not GamePlayer.objects.filter(game=game, user=user).exists():
            GamePlayer.objects.create(game=game, user=user, bet_ton=Decimal("0.00"))

    def get_or_create_game_and_player(self, user):
        from games.models import Game, GamePlayer
        from django.db import transaction
        from decimal import Decimal

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

    def update_bet(self, user, amount):
        from games.models import GamePlayer
        GamePlayer.objects.filter(game_id=self.game_id, user=user).update(bet_ton=amount)

    async def update_pot_and_chances(self):
        await sync_to_async(self.calc_and_save_pot_chances)()
        await self.send_game_state()

    def calc_and_save_pot_chances(self):
        from games.models import Game, GamePlayer

        game = Game.objects.prefetch_related("players").get(id=self.game_id)
        total_bet = sum([p.bet_ton for p in game.players.all()])

        for p in game.players.all():
            chance = (p.bet_ton / total_bet) * 100 if total_bet > 0 else 0
            GamePlayer.objects.filter(id=p.id).update(chance_percent=chance)

        game.pot_amount_ton = total_bet
        game.save()

    async def send_game_state(self):
        game_data = await sync_to_async(self.get_game_state)()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_state",
                **game_data
            }
        )

    def get_game_state(self):
        from games.models import Game

        game = Game.objects.prefetch_related("players__user").get(id=self.game_id)
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

    async def game_state(self, event):
        await self.send(text_data=json.dumps(event))
