# gifts/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema

from .serializers import GiftSerializer, GiftWithdrawSerializer
from .services.inventory import InventoryService
from .services.withdrawal import GiftWithdrawalService

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
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GiftWithdrawSerializer,
        responses={
            200: openapi_schema := {"type": "object", "properties": {"detail": {"type": "string"}}},
            403: openapi_schema,
            404: openapi_schema,
        },
        summary="Вывод NFT подарка",
        description="""
        Позволяет пользователю **вывести NFT из инвентаря**.  
        После успешного вывода NFT удаляется из базы данных.  
        В будущем сюда можно добавить интеграцию с TON blockchain.
        """,
    )
    def post(self, request, *args, **kwargs):
        serializer = GiftWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gift_id = serializer.validated_data["gift_id"]
        user = request.user

        result = GiftWithdrawalService.withdraw_gift(user, gift_id)
        return Response({"detail": result["detail"]}, status=result["status"])
