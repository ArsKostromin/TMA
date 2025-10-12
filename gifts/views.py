# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import InventorySerializer
from rest_framework import generics
from .services.inventory import InventoryService
from .serializers import GiftSerializer


class UserInventoryView(generics.ListAPIView):
    """
    Получить список подарков в инвентаре текущего пользователя
    """
    serializer_class = GiftSerializer  # Используем GiftSerializer вместо InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InventoryService.get_user_inventory(self.request.user)


class UserAddsGift(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Если user_id передан в данных, используем его, иначе текущего пользователя
        data = request.data.copy()
        if 'user' not in data:
            data['user'] = request.user.id
        
        serializer = GiftSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)