import json
import time
from decimal import Decimal
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .services.auth import AuthService
from .services.game import GameService


class PvpGameConsumer(AsyncWebsocketConsumer):
    RATE_LIMIT_SECONDS = 0.5  # минимальный интервал между командами

    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        self.scope["user"] = AnonymousUser()
        await self.accept()
        self.authenticated = False
        self.game_id = None
        self.room_group_name = None
        self.last_action_time = 0  # время последней команды

    async def disconnect(self, close_code):
        if self.authenticated and self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        now = time.time()
        if now - self.last_action_time < self.RATE_LIMIT_SECONDS:
            # Игнорируем спам
            await self.send(json.dumps({"error": "Too many requests"}))
            return
        self.last_action_time = now

        data = json.loads(text_data)
        action = data.get("action")

        if not self.authenticated:
            if action == "authenticate":
                token = data.get("token")
                if not token:
                    await self.close()
                    return
                user = await AuthService.get_user_from_token(token)
                if user is None or not user.is_authenticated:
                    await self.close()
                    return

                self.scope["user"] = user
                self.authenticated = True

                game_id = await sync_to_async(GameService.find_user_game)(user)
                if game_id:
                    self.game_id = game_id
                    self.room_group_name = f"pvp_{game_id}"
                    await sync_to_async(GameService.ensure_player_in_game)(user, game_id)
                else:
                    game_id, room_group_name = await sync_to_async(GameService.get_or_create_game_and_player)(user)
                    self.game_id = game_id
                    self.room_group_name = room_group_name

                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                await self.send_game_state()
            else:
                await self.close()
            return

        if action == "bet":
            user = await AuthService.get_authenticated_user(data.get("token"))
            if not user:
                await self.close()
                return

            amount = Decimal(data.get("amount", "0"))
            await sync_to_async(GameService.update_bet)(user, amount, self.game_id)
            await sync_to_async(GameService.calc_and_save_pot_chances)(self.game_id)
            await self.send_game_state()

    async def send_game_state(self):
        game_data = await sync_to_async(GameService.get_game_state)(self.game_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_state",
                **game_data
            }
        )

    async def game_state(self, event):
        await self.send(text_data=json.dumps(event))
