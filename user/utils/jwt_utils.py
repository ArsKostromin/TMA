import jwt
from datetime import datetime, timedelta
from django.conf import settings


def create_jwt(user_id: int) -> str:
    """
    Генерирует JWT-токен для пользователя.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + settings.JWT_EXP_DELTA,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
