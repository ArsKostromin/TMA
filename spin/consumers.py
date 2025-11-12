# consumers.py
import json
import logging
from decimal import Decimal
from channels.generic.websocket import AsyncWebsocketConsumer
from games.services.auth import AuthService
from .services.spin_bet_service import SpinBetService
from django.core.exceptions import ValidationError

logger = logging.getLogger('games.consumers')


class SpinGameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        self.scope["user"] = AnonymousUser()
        await self.accept()
        self.socket_id = None
        logger.info("WebSocket подключён")

    async def disconnect(self, close_code):
        if self.socket_id:
            await self.channel_layer.group_discard(f"socket_{self.socket_id}", self.channel_name)
        logger.info(f"WebSocket отключён: {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        token = data.get("token")
        socket_id = data.get("socket_id")

        if not socket_id:
            await self.send(json.dumps({"error": "socket_id required"}))
            return

        self.socket_id = socket_id
        await self.channel_layer.group_add(f"socket_{socket_id}", self.channel_name)

        # --- авторизация ---
        user = await AuthService.get_user_from_token(token)
        if not user or not user.is_authenticated:
            await self.send(json.dumps({"error": "auth failed"}))
            await self.close()
            return
        self.user = user

        # --- Сценарий 1: ставка в Stars ---
        bet_stars = data.get("bet_stars")
        if bet_stars is not None:
            try:
                invoice = await SpinBetService.create_invoice_for_stars(
                    user=self.user,
                    bet_stars=int(bet_stars),
                    socket_id = socket_id
                )
                await self.send(json.dumps({
                    "payment_url": invoice.get("payment_link"),
                    "order_id": invoice.get("order_id"),
                    "socket_id": socket_id
                }))
                return
            except ValidationError as e:
                await self.send(json.dumps({"error": str(e)}))
                return

        # --- Сценарий 2: ставка в TON ---
        bet_ton = data.get("bet_ton")
        if bet_ton is not None:
            try:
                result = await SpinBetService.create_bet_with_ton(
                    user=self.user,
                    bet_ton=Decimal(str(bet_ton))
                )
                await self.send(json.dumps({"result": result}))
                return
            except ValidationError as e:
                await self.send(json.dumps({"error": str(e)}))
                return

        await self.send(json.dumps({"error": "No valid bet provided"}))

    # сюда вебхук шлёт
    async def spin_result(self, event):
        await self.send(json.dumps({
            "type": "spin_result",
            "data": event["data"]
        }))
