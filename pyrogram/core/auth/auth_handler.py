"""
Авторизация Pyrogram-клиента через переменные окружения PHONE_NUMBER и LOGIN_CODE
"""
import logging
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired
from config import PHONE_NUMBER, LOGIN_CODE

logger = logging.getLogger(__name__)


async def authorize_with_code(app):
    """
    Авторизует клиента по номеру и коду (из .env).
    При первом запуске — отправляет код и ждёт, пока ты добавишь его в LOGIN_CODE и перезапустишь контейнер.
    При последующих запусках — использует сохранённую сессию.
    """
    if not PHONE_NUMBER:
        logger.error("❌ PHONE_NUMBER не задан в переменных окружения.")
        return False

    try:
        # Проверим, уже ли залогинен
        me = await app.get_me()
        if me:
            logger.info(f"✅ Уже авторизован как {me.first_name} (@{me.username})")
            return True
    except Exception:
        pass

    try:
        logger.info(f"📱 Отправляю код авторизации на номер: {PHONE_NUMBER}")
        sent = await app.send_code(PHONE_NUMBER)

        if not LOGIN_CODE:
            logger.warning("💡 LOGIN_CODE не установлен — добавь код из SMS в .env и перезапусти контейнер.")
            return False

        logger.info("🔑 Авторизуюсь с кодом из переменных окружения...")
        await app.sign_in(PHONE_NUMBER, sent.phone_code_hash, LOGIN_CODE)
        logger.info("✅ Авторизация успешна, сессия сохранена!")
        return True

    except PhoneCodeInvalid:
        logger.error("❌ Неверный код авторизации. Проверь LOGIN_CODE.")
        return False
    except PhoneCodeExpired:
        logger.error("❌ Код авторизации истёк. Получи новый и перезапусти контейнер.")
        return False
    except SessionPasswordNeeded:
        logger.error("❌ Требуется пароль 2FA. Добавь его поддержку в коде.")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        return False


async def check_authorization_status(app):
    """
    Проверяет, авторизован ли клиент.
    """
    try:
        me = await app.get_me()
        return me is not None
    except Exception:
        return False
