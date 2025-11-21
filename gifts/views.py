# gifts/views.py
import logging
import json
import requests
import ipaddress

from decimal import Decimal
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import GiftSerializer, GiftWithdrawSerializer
from .services.inventory import InventoryService
from .services.withdrawal import GiftWithdrawalService
from .services.withdrawal_request import GiftWithdrawalRequestService
from .services.userbot_client import send_test_request_to_userbot
from .utils.telegram_payments import create_stars_invoice
from user.models import User


logger = logging.getLogger(__name__)


class UserInventoryView(generics.ListAPIView):
    """
    Получить список подарков в инвентаре текущего пользователя
    """
    serializer_class = GiftSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: GiftSerializer(many=True)},
        summary="Инвентарь пользователя",
        description="Возвращает список NFT-подарков, принадлежащих текущему аутентифицированному пользователю."
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        logger.info(f"[Inventory] Запрос списка подарков для пользователя {user.id}")
        gifts = InventoryService.get_user_inventory(user)
        serializer = GiftSerializer(gifts, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAddsGift(APIView):
    permission_classes = [AllowAny]  # TODO: заменить на авторизацию по токену/подписи

    @extend_schema(
        request=GiftSerializer,
        responses={201: GiftSerializer},
        summary="Добавление NFT подарка",
        description="""
        Добавляет NFT-подарок в инвентарь пользователя.
        Если подарок с таким `ton_contract_address` уже существует — обновляет его данные.
        """,
    )
    def post(self, request):
        logger.info("[UserAddsGift] POST-запрос на добавление подарка")
        logger.info(f"[UserAddsGift] Body: {request.data}")

        try:
            data = request.data.copy()
            if "user" not in data:
                data["user"] = request.user.id if request.user.is_authenticated else None
                logger.info(f"[UserAddsGift] user_id взят из request.user: {data['user']}")
            else:
                logger.info(f"[UserAddsGift] user_id явно передан: {data['user']}")

            serializer = GiftSerializer(data=data, context={"request": request})
            serializer.is_valid(raise_exception=True)

            gift = serializer.save()
            logger.info(f"[UserAddsGift] 🎁 Подарок сохранён: {gift.id} ({gift.name})")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception(f"[UserAddsGift] ❌ Ошибка: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawalOfNFT(APIView):
    """
    Эндпоинт для создания запроса на вывод NFT-подарка.
    Создает запрос на вывод и отправляет инвойс на оплату 25 звёзд.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создание запроса на вывод NFT подарка",
        description="Создает запрос на вывод NFT и отправляет инвойс на оплату 25 звёзд. Подарок будет выведен только после успешной оплаты.",
        request=GiftWithdrawSerializer,
        responses={
            200: OpenApiResponse(description="Запрос создан, инвойс отправлен"),
            400: OpenApiResponse(description="Ошибка данных"),
            403: OpenApiResponse(description="Подарок не принадлежит пользователю"),
            404: OpenApiResponse(description="Подарок не найден"),
            500: OpenApiResponse(description="Ошибка создания инвойса"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = GiftWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gift_id = serializer.validated_data["gift_id"]
        user = request.user

        logger.info(f"📤 Пользователь {user} запросил создание запроса на вывод NFT ID={gift_id}")

        # Создаем запрос на вывод через сервис
        result = GiftWithdrawalRequestService.create_withdrawal_request(user, gift_id)
        
        if result["status"] != status.HTTP_200_OK:
            return Response(
                {"detail": result["detail"]},
                status=result["status"]
            )

        return Response(result, status=status.HTTP_200_OK)


TELEGRAM_IP_RANGES = [
    ipaddress.ip_network("149.154.160.0/20"),
    ipaddress.ip_network("91.108.4.0/22"),
]


def ip_is_telegram(ip: str) -> bool:
    try:
        ip_addr = ipaddress.ip_address(ip)
        return any(ip_addr in net for net in TELEGRAM_IP_RANGES)
    except:
        return False


# ============================== #
#  Webhook
# ============================== #

class TelegramPaymentWebhook(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        # -------------------------------------------------
        # 1. Проверка IP Telegram
        # -------------------------------------------------
        real_ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR")
        )

        if not ip_is_telegram(real_ip):
            logger.error(f"[TPW] INVALID IP {real_ip} — NOT TELEGRAM")
            return Response({"detail": "Forbidden"}, status=403)

        # -------------------------------------------------
        # 2. Проверка Secret Token
        # -------------------------------------------------
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if secret != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.error("[TPW] INVALID SECRET TOKEN")
            return Response({"detail": "Forbidden"}, status=403)

        # -------------------------------------------------
        # Основная логика
        # -------------------------------------------------
        data = request.data
        logger.warning(f"[TPW] UPDATE: {data}")

        try:
            # ======================= pre_checkout_query ============================
            if "pre_checkout_query" in data:
                pcq = data["pre_checkout_query"]
                query_id = pcq.get("id")

                logger.warning(f"[TPW] pre_checkout_query: {pcq}")

                requests.post(
                    f"https://api.telegram.org/bot{settings.BOT_TOKEN}/answerPreCheckoutQuery",
                    json={"pre_checkout_query_id": query_id, "ok": True},
                    timeout=5,
                )

                return Response({"detail": "pre_checkout_query OK"}, status=200)

            # ======================= successful_payment ============================
            if "message" in data and "successful_payment" in data["message"]:
                msg = data["message"]
                payment = msg["successful_payment"]

                payload_raw = payment.get("invoice_payload")
                amount_raw = payment.get("total_amount")  
                telegram_user = msg["from"]["id"]

                logger.warning(
                    f"[TPW] successful_payment payload={payload_raw}, amount={amount_raw}"
                )

                # ----------- разбор payload -----------
                user_id = None

                if payload_raw:
                    try:
                        payload = json.loads(payload_raw)
                        if isinstance(payload, dict):
                            user_id = (
                                payload.get("payload", {}).get("user_id")
                                or payload.get("user_id")
                            )
                    except Exception:
                        if isinstance(payload_raw, str) and "_" in payload_raw:
                            maybe_id = payload_raw.split("_")[-1]
                            if maybe_id.isdigit():
                                user_id = int(maybe_id)

                if not user_id:
                    user_id = telegram_user

                # ----------- ищем юзера -----------
                try:
                    user = User.objects.get(telegram_id=user_id)
                except User.DoesNotExist:
                    logger.error(f"[TPW] user {user_id} not found")
                    return Response({"detail": "User not found"}, status=404)

                # ----------- конверсия -----------
                stars = int(amount_raw) # XTR → Stars

                # ----------- пополнение баланса -----------
                user.add_stars(stars)

                logger.warning(f"[TPW] BALANCE +{stars}⭐ for user={user_id}")

                return Response(
                    {"detail": f"Баланс пополнен на {stars}⭐"}, status=200
                )

            # ======================= неизвестное ============================
            return Response({"detail": "Unknown update"}, status=200)

        except Exception as e:
            logger.exception(f"[TPW] Ошибка: {e}")
            return Response({"detail": str(e)}, status=500)
            