# views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from drf_yasg.utils import swagger_auto_schema
from .serializers import GiftSerializer, WithdrawGiftRequestSerializer
from .services.userbot_client import UserbotClient
from transactions.models import Transaction
from decimal import Decimal
from .services.inventory import InventoryService

logger = logging.getLogger(__name__)

class UserInventoryView(generics.ListAPIView):
    """
    Получить список подарков в инвентаре текущего пользователя
    """
    serializer_class = GiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        logger.info(f"[Inventory] Запрос списка подарков для пользователя {user.id if user.is_authenticated else 'Anonymous'}")
        return InventoryService.get_user_inventory(user)


class UserAddsGift(APIView):
    permission_classes = [AllowAny]  # можно потом заменить на кастомную проверку токена

    @swagger_auto_schema(request_body=GiftSerializer)
    def post(self, request):
        logger.info("[UserAddsGift] Входящий POST-запрос на добавление подарка")
        logger.info(f"[UserAddsGift] Headers: {request.headers}")
        logger.info(f"[UserAddsGift] Body: {request.data}")

        try:
            data = request.data.copy()

            if 'user' not in data:
                data['user'] = request.user.id if request.user.is_authenticated else None
                logger.info(f"[UserAddsGift] user_id взят из request.user: {data['user']}")
            else:
                logger.info(f"[UserAddsGift] user_id явно передан: {data['user']}")

            serializer = GiftSerializer(data=data, context={"request": request})
            if not serializer.is_valid():
                logger.error(f"[UserAddsGift] Ошибка валидации: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            gift = serializer.save()
            logger.info(f"[UserAddsGift] 🎁 Подарок успешно сохранён: {gift.id} ({gift.name})")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception(f"[UserAddsGift] ❌ Неожиданная ошибка: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawGiftView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=WithdrawGiftRequestSerializer)
    def post(self, request):
        """
        Эндпоинт вывода подарка с инвентаря пользователя на его Telegram-аккаунт через userbot.
        Шаги:
          1) Валидация данных (проверка владения подарком и Stars)
          2) Вызов userbot API для передачи подарка
          3) При успехе: списать 25 Stars, записать транзакцию, отвязать подарок (user=None)
        """
        serializer = WithdrawGiftRequestSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user_instance"]
        gift = serializer.validated_data["gift_instance"]
        to_telegram_id = serializer.validated_data["to_telegram_id"]
        fee_stars = int(serializer.validated_data.get("fee_stars", 25))

        # 2) Вызов userbot
        transfer_res = UserbotClient.transfer_gift(
            to_telegram_id=to_telegram_id,
            gift_contract_address=gift.ton_contract_address,
            fee_stars=fee_stars,
        )

        if not transfer_res.ok:
            return Response(
                {"detail": transfer_res.error or "Не удалось передать подарок"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 3) Списание Stars и фиксация транзакции
        try:
            user.subtract_stars(fee_stars)
            Transaction.objects.create(
                user=user,
                tx_type="commission",
                amount=Decimal(fee_stars),
                currency="Stars",
                description=f"Комиссия за передачу подарка {gift.ton_contract_address}",
            )
        except Exception as e:
            # Если не получилось списать — вернём ошибку (теоретически не должно случиться после валидации)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 4) Убираем владение подарком (считаем, что ушёл в Telegram инвентарь пользователя)
        gift.user = None
        gift.save(update_fields=["user", "updated_at"])

        return Response(
            {
                "ok": True,
                "gift": {
                    "ton_contract_address": gift.ton_contract_address,
                    "name": gift.name,
                },
                "transfer": transfer_res.data or {},
                "balance_stars": user.balance_stars,
            },
            status=status.HTTP_200_OK,
        )