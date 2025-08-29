from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from .services.auth import AuthService
from .services.telegram_auth import TelegramAuthService
from django.conf import settings
from .utils.telegram_auth import validate_init_data, get_user_avatar, parse_init_data_no_check
from .serializers import (
    RefreshTokenRequestSerializer,
    RefreshTokenResponseSerializer,
    LogoutResponseSerializer,
    TelegramAuthRequestSerializer, 
    TelegramAuthResponseSerializer,
    UserBalanceSerializer
)

User = get_user_model()

class TelegramAuthView(APIView):
    @extend_schema(
        request=TelegramAuthRequestSerializer,
        responses={200: TelegramAuthResponseSerializer},
        summary="Telegram authentication"
    )
    def post(self, request):
        serializer = TelegramAuthRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        init_data = serializer.validated_data["initData"]

        try:
            result = TelegramAuthService.authenticate(init_data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        response_serializer = TelegramAuthResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    @extend_schema(
        request=RefreshTokenRequestSerializer,
        responses={200: RefreshTokenResponseSerializer},
        summary="Обновление access-токена",
        description="Принимает refresh токен и возвращает новый access токен.",
    )
    def post(self, request):
        serializer = RefreshTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["refresh"]

        try:
            payload = AuthService.decode_token(token)
            if payload.get("type") != "refresh":
                return Response({"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        access = AuthService.create_access_token(payload["user_id"])
        return Response({"access": access}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    @extend_schema(
        responses={200: LogoutResponseSerializer},
        summary="Выход из системы",
        description="Фактически ничего не делает (refresh токен не инвалидируется), просто возвращает сообщение."
    )
    def post(self, request):
        return Response({"message": "Logged out"}, status=status.HTTP_200_OK)


class UserBalanceView(APIView):
    @extend_schema(
        responses={200: UserBalanceSerializer},
        summary="Получение баланса пользователя",
        description="Возвращает текущий баланс TON и Stars для аутентифицированного пользователя."
    )
    def get(self, request):
        user = request.user
        serializer = UserBalanceSerializer({
            'balance_ton': user.balance_ton,
            'balance_stars': user.balance_stars
        }, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)