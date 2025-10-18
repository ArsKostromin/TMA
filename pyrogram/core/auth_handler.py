"""
Модуль для авторизации Pyrogram-клиента
Работает через переменные окружения PHONE_NUMBER и LOGIN_CODE
"""
import logging
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired
from config import PHONE_NUMBER, LOGIN_CODE

logger = logging.getLogger(__name__)


async def authorize_with_code(app):
    """
    Авторизует клиента по номеру и коду (из .env)
    Возвращает True, если всё ок.
    """
    if not PHONE_NUMBER:
        logger.error("❌ PHONE_NUMBER не задан в переменных окружения.")
        return False

    try:
        logger.info(f"📱 Отправляю код авторизации на номер: {PHONE_NUMBER}")
        sent = await app.send_code(PHONE_NUMBER)

        if not LOGIN_CODE:
            logger.error("❌ LOGIN_CODE не установлен.")
            logger.error("💡 Получи код из SMS и добавь его в .env")
            return False

        logger.info("🔑 Авторизуюсь с кодом из переменных окружения...")
        await app.sign_in(PHONE_NUMBER, sent.phone_code_hash, LOGIN_CODE)

        logger.info("✅ Авторизация успешна!")
        return True

    except PhoneCodeInvalid:
        logger.error("❌ Неверный код авторизации.")
        return False
    except PhoneCodeExpired:
        logger.error("❌ Код авторизации истёк.")
        return False
    except SessionPasswordNeeded:
        logger.error("❌ Требуется пароль 2FA. Отключи 2FA или добавь поддержку пароля.")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        return False


async def check_authorization_status(app):
    """
    Проверяет, авторизован ли клиент
    """
    try:
        me = await app.get_me()
        return me is not None
    except Exception:
        return False
