import jwt
import time
from django.conf import settings
from django.contrib.auth import get_user_model

class AuthService:
    @staticmethod
    def create_access_token(user_id):
        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + int(settings.JWT_ACCESS_LIFETIME.total_seconds()),
            "type": "access",
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id):
        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + int(settings.JWT_REFRESH_LIFETIME.total_seconds()),
            "type": "refresh",
        }
        return jwt.encode(payload, settings.JWT_SECRET_2, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token):
        for secret in [settings.JWT_SECRET, settings.JWT_SECRET_2]:
            try:
                return jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
            except jwt.ExpiredSignatureError:
                raise ValueError("Token expired")
            except jwt.InvalidTokenError:
                continue
        raise ValueError("Invalid token")

    @staticmethod
    def authenticate_telegram(telegram_id, username=None):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=f"tg_{telegram_id}",
            defaults={"telegram_id": telegram_id}
        )
        if username and user.username != username:
            user.username = username
            user.save()
        return user
