import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction
from django.contrib.auth import get_user_model
from games.models import Game, GamePlayer
from decimal import Decimal

User = get_user_model()

class PvpGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # Находим или создаём игру
        async with transaction.atomic():
            game = (
                Game.objects
                .filter(status="waiting", mode="pvp")
                .select_for_update()
                .first()
            )
            if not game:
                game = Game.objects.create(mode="pvp", status="waiting")

            self.game_id = game.id
            self.room_group_name = f"pvp_{self.game_id}"

            # Добавляем игрока, если его ещё нет
            if not GamePlayer.objects.filter(game=game, user=user).exists():
                GamePlayer.objects.create(
                    game=game,
                    user=user,
                    bet_ton=Decimal("0.00"),  # Пока без ставки
                )

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send_game_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Тут можно принимать действия от клиента:
        - сделать ставку
        - поставить подарок
        """
        data = json.loads(text_data)
        action = data.get("action")

        if action == "bet":
            amount = Decimal(data.get("amount", "0"))
            user = self.scope["user"]
            GamePlayer.objects.filter(game_id=self.game_id, user=user).update(bet_ton=amount)

            # Пересчёт банка и шансов
            await self.update_pot_and_chances()

    async def update_pot_and_chances(self):
        game = Game.objects.prefetch_related("players").get(id=self.game_id)
        total_bet = sum([p.bet_ton for p in game.players.all()])

        for p in game.players.all():
            if total_bet > 0:
                chance = (p.bet_ton / total_bet) * 100
            else:
                chance = 0
            GamePlayer.objects.filter(id=p.id).update(chance_percent=chance)

        game.pot_amount_ton = total_bet
        game.save()

        await self.send_game_state()

    async def send_game_state(self):
        """Отправляем всем в комнате текущее состояние игры"""
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

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_state",
                "game_id": game.id,
                "status": game.status,
                "pot_amount_ton": str(game.pot_amount_ton),
                "players": players_data,
            }
        )

    async def game_state(self, event):
        await self.send(text_data=json.dumps(event))
