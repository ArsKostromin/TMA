import json
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .models import SpinGame, SpinWheelSector
from .serializers import (
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayRequestSerializer,
    SpinPlayResponseSerializer,
)
from .api_examples import (
    SPIN_WHEEL_EXAMPLE,
    SPIN_GAME_HISTORY_EXAMPLE,
)
from spin.services.spin_service import SpinService
from spin.services.telegram_stars import SocketNotifyService


logger = logging.getLogger("games.webhook")


class TelegramStarsWebhookView(APIView):
    """
    Принимает вебхук от Telegram Stars после успешной оплаты.
    Извлекает payload (channel_name) и уведомляет WebSocket.
    """

    def post(self, request, *args, **kwargs):
        data = request.data
        logger.info(f"🌠 Webhook received: {data}")

        # --- Проверяем наличие успешного платежа ---
        try:
            payment = data.get("message", {}).get("successful_payment", {})
            if not payment:
                logger.warning("⚠️ Нет поля successful_payment — пропускаем")
                return JsonResponse({"error": "no successful_payment"}, status=400)
        except Exception as e:
            logger.exception("❌ Ошибка при обработке вебхука")
            return JsonResponse({"error": str(e)}, status=400)

        # --- Достаём payload из инвойса ---
        invoice_payload_raw = payment.get("invoice_payload")
        if not invoice_payload_raw:
            logger.warning("⚠️ Нет invoice_payload в вебхуке")
            return JsonResponse({"error": "missing invoice_payload"}, status=400)

        try:
            payload_data = json.loads(invoice_payload_raw)
        except json.JSONDecodeError:
            logger.error(f"❌ Ошибка парсинга payload: {invoice_payload_raw}")
            payload_data = {}

        # ожидаем {"type": "spin_game", "payload": "имя канала22"}
        socket_id = payload_data.get("payload")
        if not socket_id:
            logger.warning("⚠️ Webhook без channel_name/payload — пропускаем")
            return JsonResponse({"error": "missing channel_name"}, status=400)

        total_amount = payment.get("total_amount")
        currency = payment.get("currency")

        # --- Уведомляем WebSocket ---
        try:
            SocketNotifyService.send_to_socket(
                socket_id=socket_id,
                event_type="spin_result",
                data={
                    "status": "success",
                    "message": "Оплата подтверждена, можно запускать игру 🎰",
                    "amount": total_amount,
                    "currency": currency,
                },
            )
            logger.info(f"✅ Уведомление отправлено в канал: {socket_id}")
        except Exception as e:
            logger.exception(f"❌ Ошибка при отправке в сокет: {e}")
            return JsonResponse({"error": "socket_send_failed"}, status=500)

        return JsonResponse({"ok": True})


class SpinWheelView(APIView):
    """
    Получение всех секторов колеса для спина
    """
    
    @extend_schema(
        summary="Сектора колеса спина",
        description="Возвращает все сектора колеса спина с подарками и вероятностями",
        responses={
            200: OpenApiResponse(
                response=SpinWheelSectorSerializer(many=True),
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=SPIN_WHEEL_EXAMPLE
                    )
                ],
            ),
        },
        tags=["spin"],
    )
    def get(self, request):
        # Берём все сектора, сортируя по индексу
        sectors = SpinWheelSector.objects.select_related("gift").all().order_by("index")
        serializer = SpinWheelSectorSerializer(sectors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpinGameHistoryView(ListAPIView):
    serializer_class = SpinGameHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="История игр в спин",
        description="Возвращает историю всех игр в спин для текущего пользователя",
        responses={
            200: OpenApiResponse(
                response=SpinGameHistorySerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=SPIN_GAME_HISTORY_EXAMPLE
                    )
                ],
            ),
        },
        tags=["spin"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            SpinGame.objects
            .select_related("gift_won")
            .order_by("-played_at")
        )
