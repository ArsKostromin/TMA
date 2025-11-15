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
    SPIN_PLAY_RESPONSE_EXAMPLE
)
from spin.services.spin_service import SpinService
from django.db import transaction


logger = logging.getLogger("games.webhook")


class TelegramStarsWebhookView(APIView):
    """
    Принимает вебхук от Telegram Stars после успешной оплаты.
    Извлекает payload (channel_name) и уведомляет WebSocket.
    """

    def post(self, request, *args, **kwargs):
        data = request.data
        logger.info(f"🌠 Webhook received: {data}")



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


class SpinPlayView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Игра в спин",
        description="Запускает игру в спин с указанными ставками в Stars и TON",
        request=SpinPlayRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SpinPlayResponseSerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=SPIN_PLAY_RESPONSE_EXAMPLE
                    )
                ],
            ),
            400: OpenApiResponse(description="Ошибка валидации"),
        },
        tags=["Games"],
    )
    def post(self, request):
        serializer = SpinPlayRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        bet_stars = data.get("bet_stars", 0)
        bet_ton = data.get("bet_ton", Decimal("0"))

        try:
            SpinService.validate_bet(bet_stars, bet_ton)

            with transaction.atomic():
                # ловим недостаточно баланса
                try:
                    game, sector = SpinService.play(
                        user,
                        bet_stars=bet_stars,
                        bet_ton=bet_ton
                    )
                except ValueError as e:
                    # превращаем в красивую ошибку 400
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                result = {
                    "game_id": game.id,
                    "payment_required": False,
                    "payment_link": None,
                    "bet_stars": bet_stars,
                    "bet_ton": str(bet_ton),
                    "result_sector": sector.index,
                    "gift_won": sector.gift,
                    "balances": {
                        "stars": user.balance_stars,
                        "ton": str(user.balance_ton),
                    }
                }

            response_data = format_spin_response(result)
            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Spin play error")
            return Response({"error": "Internal error"}, status=500)