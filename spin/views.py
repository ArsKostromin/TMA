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

from .models import SpinGame, SpinWheelSector
from .serializers import (
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayRequestSerializer,
    SpinPlayResponseSerializer,
)
from spin.services.spin_service import SpinService


from .api_examples import (
    spin_wheel_schema,
    spin_history_schema,
    spin_play_schema,
)
from .services.spin_bet_service import SpinBetService
from .utils.spin_response import format_spin_response


logger = logging.getLogger("games.webhook")


class TelegramStarsWebhookView(APIView):
    """
    Принимает вебхук от Telegram Stars после успешной оплаты.
    Извлекает payload (channel_name) и уведомляет WebSocket.
    """
    def post(self, request, *args, **kwargs):
        data = request.data
        logger.info(f"Webhook received: {data}")
        return Response({"ok": True})


@spin_wheel_schema
class SpinWheelView(APIView):
    def get(self, request):
        sectors = SpinWheelSector.objects.select_related("gift").all().order_by("index")
        serializer = SpinWheelSectorSerializer(sectors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@spin_history_schema
class SpinGameHistoryView(ListAPIView):
    serializer_class = SpinGameHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            SpinGame.objects
            .select_related("gift_won")
            .order_by("-played_at")
        )


@spin_play_schema
class SpinPlayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SpinPlayRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        bet_stars = data.get("bet_stars", 0)
        bet_ton = data.get("bet_ton", Decimal("0"))

        try:
            # Валидируем ставку
            SpinService.validate_bet(bet_stars, bet_ton)

            # Обрабатываем ставку
            if bet_stars > 0:
                result = SpinBetService.create_bet_with_stars(user, bet_stars)
            elif bet_ton > 0:
                result = SpinBetService.create_bet_with_ton(user, bet_ton)
            else:
                return Response(
                    {"error": "Нужна ставка в Stars или TON"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response_data = format_spin_response(result)
            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
