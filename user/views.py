from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from utils.telegram_auth import validate_init_data, get_user_avatar

User = get_user_model()

class TelegramAuthView(APIView):
    def post(self, request):
        init_data = request.data.get("initData")
        if not init_data:
            return Response({"error": "initData is required"}, status=400)

        try:
            data = validate_init_data(init_data)
        except ValueError as e:
            return Response({"error": str(e)}, status=403)

        tg_user = data["user"]
        avatar_url = get_user_avatar(tg_user["id"])

        user, _ = User.objects.get_or_create(
            telegram_id=tg_user["id"],
            defaults={
                "username": tg_user.get("username", ""),
                "first_name": tg_user.get("first_name", ""),
                "last_name": tg_user.get("last_name", ""),
                "avatar_url": avatar_url
            }
        )

        # здесь можешь прикрутить JWT
        return Response({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "avatar_url": avatar_url
        })
