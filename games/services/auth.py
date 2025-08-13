from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

class AuthService:
    @staticmethod
    async def get_user_from_token(token):
        try:
            import jwt
            from django.conf import settings
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                return None
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)
            return user
        except Exception:
            return None

    @staticmethod
    async def get_authenticated_user(token: str):
        """
        Возвращает авторизованного пользователя по JWT-токену или None.
        """
        try:
            import jwt
            from django.conf import settings

            if not token:
                return None

            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get("user_id")
            if not user_id:
                return None

            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)

            # если пользователь деактивирован или гость
            if not getattr(user, "is_authenticated", False):
                return None

            return user
        except Exception:
            return None