from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .services.auth import AuthService
from django.conf import settings
from .utils.telegram_auth import validate_init_data, get_user_avatar, parse_init_data_no_check

User = get_user_model()

class TelegramAuthView(APIView):
    def post(self, request):
        init_data = request.data.get("initData")
        if not init_data:
            return Response({"error": "initData is required"}, status=400)

        try:
            if settings.DEBUG:
                data = parse_init_data_no_check(init_data)  # dev-режим, без подписи
            else:
                data = validate_init_data(init_data)  # prod — с проверкой HMAC
        except ValueError as e:
            return Response({"error": str(e)}, status=403)

        tg_user = data.get("user")
        if not tg_user:
            return Response({"error": "No user data in initData"}, status=400)

        avatar_url = get_user_avatar(tg_user["id"])

        user, created = User.objects.get_or_create(
            telegram_id=tg_user["id"],
            defaults={
                "username": tg_user.get("username", ""),
                "avatar_url": avatar_url
            }
        )

        if not created:
            updated = False
            if user.username != tg_user.get("username", ""):
                user.username = tg_user.get("username", "")
                updated = True
            if user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
                updated = True
            if updated:
                user.save()

        access = AuthService.create_access_token(user.id)
        refresh = AuthService.create_refresh_token(user.id)

        return Response({
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "access": access,
            "refresh": refresh
        })


class RefreshTokenView(APIView):
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"error": "refresh token required"}, status=400)

        try:
            payload = AuthService.decode_token(token)
            if payload.get("type") != "refresh":
                return Response({"error": "Invalid token type"}, status=400)
        except ValueError as e:
            return Response({"error": str(e)}, status=401)

        access = AuthService.create_access_token(payload["user_id"])
        return Response({"access": access})


class LogoutView(APIView):
    def post(self, request):
        # Можно реализовать blacklist refresh токенов, но тут просто ответим
        return Response({"message": "Logged out"})
