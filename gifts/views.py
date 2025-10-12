# views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from drf_yasg.utils import swagger_auto_schema
from .serializers import GiftSerializer
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
