import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils.telegram_auth import validate_init_data, get_user_avatar, parse_init_data_no_check

User = get_user_model()


class TelegramAuthView(APIView):
    def post(self, request):
        init_data = request.data.get("initData")
        if not init_data:
            return Response({"error": "initData is required"}, status=400)

        try:
            # data = validate_init_data(init_data) 
            data = parse_init_data_no_check(init_data) #на проде убрать 
        except ValueError as e:
            return Response({"error": str(e)}, status=403)

        tg_user = data["user"]
        avatar_url = get_user_avatar(tg_user["id"])

        user, created = User.objects.get_or_create(
            telegram_id=tg_user["id"],
            defaults={
                "username": tg_user.get("username", ""),
                "avatar_url": avatar_url
            }
        )

        # 🔄 Если пользователь уже существовал — обновим данные
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

        payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + settings.JWT_EXP_DELTA
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return Response({
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "token": token
        })
