# consumers.py
import json
import time
from decimal import Decimal
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .services.auth import AuthService
from .services.game import GameService
from django.core.exceptions import ValidationError
# from games.services.bet_service import BetService

class PvpGameConsumer(AsyncWebsocketConsumer):
    RATE_LIMIT_SECONDS = 0.5

    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        self.scope["user"] = AnonymousUser()
        await self.accept()
        self.authenticated = False
        self.game_id = None
        self.room_group_name = None
        self.last_action_time = 0

    async def disconnect(self, close_code):
        if self.authenticated and self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        from games.services.bet_service import BetService

        now = time.time()
        if now - getattr(self, "last_action_time", 0) < self.RATE_LIMIT_SECONDS:
            await self.send(json.dumps({"error": "Too many requests"}))
            return
        self.last_action_time = now

        data = json.loads(text_data)
        action = data.get("action")

        # ещё не авторизован
        if not getattr(self, "authenticated", False):
            if action == "authenticate":
                token = data.get("token")
                if not token:
                    await self.close()
                    return

                user = await AuthService.get_user_from_token(token)
                if not user or not user.is_authenticated:
                    await self.close()
                    return

                # сохраняем авторизацию
                self.scope["user"] = user
                self.user = user
                self.authenticated = True

                # ищем или создаём игру
                game_id = await sync_to_async(GameService.find_user_game)(user)
                if not game_id:
                    game_id, room_group_name = await sync_to_async(
                        GameService.get_or_create_game_and_player
                    )(user)
                else:
                    room_group_name = f"pvp_{game_id}"
                    await sync_to_async(GameService.ensure_player_in_game)(user, game_id)

                self.game_id = game_id
                self.room_group_name = room_group_name
                await self.channel_layer.group_add(self.room_group_name, self.channel_name)

                # регаем игрока
                await sync_to_async(GameService.add_player_to_game)(self.game_id, user)

                await self.send_game_state()
            else:
                await self.close()
            return

        # уже авторизован
        if action == "bet":
            amount = Decimal(str(data.get("amount", "0")))
            try:
                await sync_to_async(BetService.place_bet_ton)(self.user, self.game_id, amount)
                await sync_to_async(GameService.calc_and_save_pot_chances)(self.game_id)
                await self.send_game_state()
            except ValidationError as e:
                msg = e.messages[0] if hasattr(e, "messages") else str(e)
                await self.send(json.dumps({"error": msg}))

        if action == "bet_gift":
            gift_ids = data.get("gift_ids", [])  # список ID подарков
            try:
                await sync_to_async(BetService.place_bet_gifts)(self.user, self.game_id, gift_ids)
                await sync_to_async(GameService.calc_and_save_pot_chances)(self.game_id)
                await self.send_game_state()
            except ValidationError as e:
                msg = e.messages[0] if hasattr(e, "messages") else str(e)
                await self.send(json.dumps({"error": msg}))
                
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

    async def game_finished(self, event):
        await self.send(text_data=json.dumps(event))

    async def timer_started(self, event):
        await self.send(json.dumps({
            "type": "timer_started",
            "duration": event["duration"]
        }))

    async def timer_update(self, event):
        await self.send(json.dumps({
            "type": "timer_update",
            "remaining": event["remaining"]
        }))
