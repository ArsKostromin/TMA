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
    """
    Полностью автоматическая авторизация Pyrogram без input().
    Все данные берутся из config.py (переменных окружения).
    """
    try:
        logger.info("🚀 Инициализация Pyrogram клиента...")

        # имя сессии без .session
        session_name = SESSION_PATH.replace(".session", "")
        session_dir = os.path.dirname(SESSION_PATH) or "."

        app = Client(
            name=session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=session_dir
        )

        await app.connect()

        try:
            me = await app.get_me()
            if me:
                logger.info(f"✅ Уже авторизован как {me.first_name} (@{me.username})")
                return app
        except Exception:
            pass

        if not PHONE_NUMBER:
            raise ValueError("❌ PHONE_NUMBER не указан в переменных окружения")

        logger.info(f"📱 Отправляю код на {PHONE_NUMBER}...")
        sent = await app.send_code(PHONE_NUMBER)

        if not LOGIN_CODE:
            raise ValueError("❌ LOGIN_CODE не задан. Добавь его в .env и перезапусти контейнер")

        logger.info("🔑 Пробую войти с LOGIN_CODE из конфига...")
        await app.sign_in(PHONE_NUMBER, sent.phone_code_hash, LOGIN_CODE)
        logger.info("✅ Авторизация прошла успешно, сессия сохранена!")

        return app

    except PhoneCodeInvalid:
        logger.error("❌ Неверный код авторизации. Проверь LOGIN_CODE.")
    except PhoneCodeExpired:
        logger.error("❌ Код авторизации истёк. Получи новый и перезапусти.")
    except SessionPasswordNeeded:
        logger.error("❌ Включена 2FA. Нужно добавить пароль (не реализовано).")
    except Exception as e:
        logger.error(f"💥 Ошибка при инициализации клиента: {e}")
    finally:
        try:
            await app.disconnect()
        except Exception:
            pass

    return None