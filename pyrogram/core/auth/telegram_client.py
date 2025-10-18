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


async def initialize_client():
    try:
        logger.info("🚀 Инициализация Pyrogram клиента...")

        # путь к сессии
        session_name = SESSION_PATH.replace(".session", "")

        app = Client(
            session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=os.path.dirname(SESSION_PATH) or "."
        )

        await app.connect()

        if not await app.get_me():
            logger.info("🔐 Первая авторизация...")

            # если логин-код заранее передан (например через env)
            if LOGIN_CODE:
                await app.sign_in(PHONE_NUMBER, LOGIN_CODE)
                logger.info("✅ Авторизация по LOGIN_CODE выполнена.")
            else:
                # если кода нет, просим его из Telegram (первый запуск)
                sent = await app.send_code(PHONE_NUMBER)
                logger.info("📨 Код отправлен в Telegram.")

                code = input("Введите код из Telegram: ")
                await app.sign_in(PHONE_NUMBER, code, phone_code_hash=sent.phone_code_hash)

        me = await app.get_me()
        logger.info(f"🎯 Клиент успешно запущен: @{me.username}")

        return app

    except Exception as e:
        logger.error(f"💥 Ошибка инициализации клиента: {e}")
        raise