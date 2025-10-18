"""
Модуль для создания и инициализации Pyrogram клиента
"""
import logging
from pyrogram import Client
from config import API_ID, API_HASH, SESSION_PATH, PHONE_NUMBER, LOGIN_CODE
from .auth_handler import authorize_with_code, check_authorization_status

logger = logging.getLogger(__name__)


def create_client():
    """
    Создаёт клиент Pyrogram
    """
    if not API_ID or not API_HASH:
        raise ValueError("❌ Не заданы переменные окружения API_ID и API_HASH")

    logger.info("⚙️ Создаю клиент Pyrogram...")
    return Client(
        SESSION_PATH,
        api_id=int(API_ID),
        api_hash=API_HASH
    )


async def initialize_client(app):
    """
    Инициализация клиента и авторизация при необходимости
    """
    await app.connect()

    if not await check_authorization_status(app):
        logger.info("🔐 Сессия отсутствует, начинаю авторизацию...")
        ok = await authorize_with_code(app)
        if not ok:
            await app.disconnect()
            return False

    me = await app.get_me()
    user = f"{me.first_name or ''} (@{me.username})" if me else "Unknown"
    logger.info(f"✅ Авторизация успешна под аккаунтом: {user.strip()}")
    return True
