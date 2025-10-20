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
    Эндпоинт для вывода (удаления) NFT-подарка.
    Перед выполнением вывода — создаёт оплату на 25 звёзд (XTR).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Вывод NFT подарка с оплатой 25⭐",
        description="Перед выводом NFT создаёт Telegram-инвойс на 25 звёзд (Stars).",
        request=GiftWithdrawSerializer,
        responses={
            200: OpenApiResponse(description="Инвойс отправлен пользователю"),
            400: OpenApiResponse(description="Ошибка данных"),
            500: OpenApiResponse(description="Ошибка взаимодействия с Telegram или userbot"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = GiftWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gift_id = serializer.validated_data["gift_id"]
        user = request.user

        logger.info(f"📤 Пользователь {user} запросил вывод NFT ID={gift_id}")

        # Создаём инвойс на 25 звёзд
        invoice = create_stars_invoice(user, gift_id, amount=25)
        if not invoice.get("ok"):
            logger.error(f"💀 Не удалось создать инвойс: {invoice.get('error')}")
            return Response(
                {"detail": f"Ошибка при создании инвойса: {invoice.get('error')}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Отправляем уведомление userbot’у
        send_test_request_to_userbot({
            "user_id": user.id,
            "username": user.username,
            "gift_id": gift_id,
            "invoice_payload": invoice["payload"]["payload"],
        })

        return Response({
            "detail": "Инвойс успешно отправлен пользователю в Telegram для оплаты 25⭐",
            "invoice_message_id": invoice["data"].get("message_id"),
        }, status=200)