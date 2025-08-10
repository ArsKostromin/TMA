from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings

from utils.telegram_auth import validate_init_data, get_user_avatar, generate_jwt

User = get_user_model()


class TelegramAuthView(APIView):
    """
    Принимает initData от Telegram WebApp, валидирует, создаёт/обновляет пользователя,
    возвращает JWT-токен и базовую инфу.
    """

    def post(self, request):
        init_data = request.data.get("initData")
        if not init_data:
            return Response({"error": "initData is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parsed = validate_init_data(init_data)
        except ValueError:
            return Response({"error": "Invalid initData"}, status=status.HTTP_403_FORBIDDEN)

        telegram_id = int(parsed.get("id"))
        username = parsed.get("username")
        first_name = parsed.get("first_name")
        last_name = parsed.get("last_name")

        user, created = User.objects.get_or_create(telegram_id=telegram_id, defaults={
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        })

        # Обновляем данные
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.avatar_url = get_user_avatar(telegram_id)
        user.save()

        token = generate_jwt(user.id)

        return Response({
            "token": token,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar_url": user.avatar_url,
            }
        })
