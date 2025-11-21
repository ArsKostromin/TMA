# gifts/views.py
import logging
import json
import requests

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


class TelegramPaymentWebhook(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        logger.warning(f"[TPW] UPDATE: {data}")

        try:
            # -----------------------------------------------------
            # 1. pre_checkout_query → надо подтвердить Телеге
            # -----------------------------------------------------
            if "pre_checkout_query" in data:
                pcq = data["pre_checkout_query"]

                query_id = pcq.get("id")
                payload_raw = pcq.get("invoice_payload")

                logger.info(f"[TPW] pre_checkout_query payload={payload_raw}")

                # Телеге говорим «yes, всё ок, можно платить»
                requests.post(
                    f"https://api.telegram.org/bot{settings.BOT_TOKEN}/answerPreCheckoutQuery",
                    json={"pre_checkout_query_id": query_id, "ok": True}
                )

                return Response({"detail": "pre_checkout_query confirmed"}, status=200)

            # -----------------------------------------------------
            # 2. Успешная оплата Stars
            # -----------------------------------------------------
            if "message" in data and "successful_payment" in data["message"]:
                payment = data["message"]["successful_payment"]

                payload_raw = payment.get("invoice_payload")
                amount_raw = payment.get("total_amount")  # XTR в тысячных
                telegram_user = data["message"]["from"]["id"]

                if not payload_raw:
                    return Response({"detail": "Нет invoice_payload"}, status=400)

                logger.info(f"[TPW] successful_payment payload={payload_raw} amount={amount_raw}")

                # payload может быть JSON, может быть просто строка
                try:
                    payload = json.loads(payload_raw)
                except:
                    payload = payload_raw

                # -----------------------------------------------------
                # Извлекаем user_id
                # -----------------------------------------------------
                if isinstance(payload, dict):
                    user_id = payload.get("payload", {}).get("user_id") or payload.get("user_id")
                elif isinstance(payload, str) and payload.startswith("topup_"):
                    user_id = int(payload.split("_")[1])
                else:
                    user_id = telegram_user  # fallback

                # -----------------------------------------------------
                # 3. Находим юзера
                # -----------------------------------------------------
                try:
                    user = User.objects.get(telegram_id=user_id)
                except User.DoesNotExist:
                    logger.error(f"[TPW] User {user_id} not found")
                    return Response({"detail": "User not found"}, status=404)

                # -----------------------------------------------------
                # 4. Stars → total_amount приходит в тысячных
                # -----------------------------------------------------
                stars = int(amount_raw / 1000)

                user.add_stars(stars)

                logger.info(f"[TPW] balance +{stars}⭐ user={user_id}")

                return Response({"detail": "Баланс пополнен"}, status=200)

            # -----------------------------------------------------
            # 5. Непонятный объект
            # -----------------------------------------------------
            return Response({"detail": "Unknown update"}, status=200)

        except Exception as e:
            logger.exception(f"[TPW] Ошибка: {e}")
            return Response({"detail": str(e)}, status=500)