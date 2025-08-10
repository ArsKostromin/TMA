import hmac
import hashlib
import json
import requests
from urllib.parse import parse_qsl, unquote
from django.conf import settings


BOT_TOKEN = settings.BOT_TOKEN  

def validate_init_data(init_data: str) -> dict:
    """
    Валидирует initData от Telegram WebApp.
    Возвращает dict с данными пользователя или кидает ValueError.
    """
    # Разбираем строку
    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    auth_hash = parsed_data.pop("hash", None)
    if not auth_hash:
        raise ValueError("Нет hash в initData")

    # Сортируем по ключу
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

    # Формируем секретный ключ
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=BOT_TOKEN.encode(),
        digestmod=hashlib.sha256
    ).digest()

    # Считаем свой HMAC
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    if calculated_hash != auth_hash:
        raise ValueError("HMAC не совпадает — initData подделан")

    # Приводим данные user к dict
    if "user" in parsed_data:
        parsed_data["user"] = json.loads(parsed_data["user"])

    return parsed_data


def get_user_avatar(user_id: int) -> str | None:
    """
    Запрашивает аватарку пользователя через Bot API.
    Возвращает полный URL или None.
    """
    r = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getUserProfilePhotos",
        params={"user_id": user_id, "limit": 1}
    ).json()

    if not r.get("ok") or not r["result"]["photos"]:
        return None

    file_id = r["result"]["photos"][0][-1]["file_id"]
    fr = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
        params={"file_id": file_id}
    ).json()

    if not fr.get("ok"):
        return None

    file_path = fr["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
