import json
from decimal import Decimal
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class PvpGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # sync функция с транзакцией и созданием игры и игрока
        game_id, room_group_name = await sync_to_async(self.get_or_create_game_and_player)(user)
        self.game_id = game_id
        self.room_group_name = room_group_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_game_state()

    def get_or_create_game_and_player(self, user):
        from games.models import Game, GamePlayer
        from django.db import transaction

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

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "bet":
            amount = Decimal(data.get("amount", "0"))
            user = self.scope["user"]
            # обновляем ставку через sync_to_async
            await sync_to_async(self.update_bet)(user, amount)
            await self.update_pot_and_chances()

    def update_bet(self, user, amount):
        from games.models import GamePlayer
        GamePlayer.objects.filter(game_id=self.game_id, user=user).update(bet_ton=amount)

    async def update_pot_and_chances(self):
        # вся логика подсчёта и обновления в sync функции
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
