import hmac
import hashlib
import urllib.parse
import requests
import jwt
from datetime import datetime, timedelta
from django.conf import settings


def validate_init_data(init_data: str) -> dict:
    """
    Валидирует initData от Telegram WebApp через HMAC-SHA256.
    Возвращает dict с данными пользователя, если всё ок.
    """
    parsed = dict(urllib.parse.parse_qsl(init_data))
    check_hash = parsed.pop("hash", None)

    # Собираем строку
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    # Ключ для HMAC
    secret_key = hashlib.sha256(settings.BOT_TOKEN.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if hmac_hash != check_hash:
        raise ValueError("Invalid initData")

    return parsed


def get_user_avatar(telegram_id: int) -> str | None:
    """
    Получает URL аватарки пользователя через Telegram Bot API.
    """
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getUserProfilePhotos"
    r = requests.get(url, params={"user_id": telegram_id, "limit": 1})
    data = r.json()
    if not data.get("ok") or not data["result"]["total_count"]:
        return None
    file_id = data["result"]["photos"][0][-1]["file_id"]
    file_path = requests.get(
        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getFile",
        params={"file_id": file_id}
    ).json()["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"


def generate_jwt(user_id: int) -> str:
    """
    Генерирует JWT-токен для пользователя.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30),  # токен живёт 30 дней
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token
