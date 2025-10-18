"""
Создание и инициализация Pyrogram клиента
"""
import os
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
        raise ValueError("❌ Не заданы API_ID и API_HASH в окружении.")

    session_file = SESSION_PATH if SESSION_PATH.endswith(".session") else f"{SESSION_PATH}.session"
    session_exists = os.path.exists(session_file)
    if session_exists:
        logger.info(f"🗝️ Найден файл сессии: {session_file}")
    else:
        logger.warning("⚠️ Сессия отсутствует — требуется авторизация по коду.")

    return Client(
        SESSION_PATH,
        api_id=int(API_ID),
        api_hash=API_HASH
    )


async def initialize_client(app):
    """
    Инициализация клиента и авторизация при необходимости
    """
    try:
        await app.start()
        logger.info("✅ Клиент успешно запущен через start()")

        if not await check_authorization_status(app):
            logger.info("🔐 Сессия невалидна — пробую авторизацию по коду.")
            ok = await authorize_with_code(app)
            if not ok:
                logger.error("❌ Авторизация не удалась.")
                return False

        me = await app.get_me()
        logger.info(f"✅ Авторизация успешна: {me.first_name} (@{me.username})")
        return True

    except Exception as e:
        logger.exception(f"💥 Ошибка инициализации клиента: {e}")
        return False
