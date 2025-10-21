# gifts/views.py
import logging
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
    """
    Webhook для обработки успешных платежей Telegram Stars.
    Вызывается Telegram при успешной оплате инвойса.
    """
    permission_classes = [AllowAny]  # Telegram webhook не требует аутентификации

    @extend_schema(
        summary="Webhook для успешных платежей Telegram Stars",
        description="Обрабатывает уведомления об успешной оплате инвойсов и выполняет вывод подарков.",
        responses={
            200: OpenApiResponse(description="Платеж обработан успешно"),
            400: OpenApiResponse(description="Ошибка данных платежа"),
            500: OpenApiResponse(description="Ошибка обработки платежа"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Обрабатывает webhook от Telegram при успешной оплате.
        Ожидает данные в формате:
        {
            "invoice_payload": "withdraw_gift_123",
            "telegram_payment_charge_id": "...",
            "provider_payment_charge_id": "..."
        }
        """
        logger.info(f"[TelegramPaymentWebhook] Получен webhook: {request.data}")
        
        try:
            invoice_payload = request.data.get("invoice_payload")
            if not invoice_payload:
                logger.error("[TelegramPaymentWebhook] ❌ Отсутствует invoice_payload")
                return Response(
                    {"detail": "Отсутствует invoice_payload"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, что это запрос на вывод подарка
            if not invoice_payload.startswith("withdraw_gift_"):
                logger.warning(f"[TelegramPaymentWebhook] ⚠️ Неизвестный payload: {invoice_payload}")
                return Response(
                    {"detail": "Неизвестный тип платежа"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Обрабатываем успешную оплату
            success = GiftWithdrawalRequestService.process_successful_payment(invoice_payload)
            
            if success:
                logger.info(f"[TelegramPaymentWebhook] ✅ Платеж обработан успешно: {invoice_payload}")
                return Response(
                    {"detail": "Платеж обработан успешно"},
                    status=status.HTTP_200_OK
                )
            else:
                logger.error(f"[TelegramPaymentWebhook] ❌ Ошибка обработки платежа: {invoice_payload}")
                return Response(
                    {"detail": "Ошибка обработки платежа"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.exception(f"[TelegramPaymentWebhook] ❌ Ошибка: {e}")
            return Response(
                {"detail": f"Ошибка обработки webhook: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )