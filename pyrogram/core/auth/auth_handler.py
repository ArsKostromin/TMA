"""
Авторизация Pyrogram-клиента через переменные окружения (PHONE_NUMBER, LOGIN_CODE, PASSWORD)
Без ручного ввода, полностью автоматическая авторизация.
"""

import logging
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired
from config import PHONE_NUMBER, LOGIN_CODE, API_ID, API_HASH
from pyrogram import Client

logger = logging.getLogger(__name__)


async def authorize_with_code(app: Client):
    """
    Авторизация клиента с использованием данных из config.py.
    Не требует никакого ввода в консоль.
    """
    if not PHONE_NUMBER:
        logger.error("❌ PHONE_NUMBER не задан в переменных окружения.")
        return False

    try:
        # Проверим, уже ли авторизован
        me = await app.get_me()
        if me:
            logger.info(f"✅ Уже авторизован как {me.first_name} (@{me.username})")
            return True
    except Exception:
        pass  # Если не залогинен — идём дальше

    try:
        # Отправляем код
        logger.info(f"📱 Отправляю код авторизации на номер: {PHONE_NUMBER}")
        sent = await app.send_code(PHONE_NUMBER)

        if not LOGIN_CODE:
            logger.error("⚠️ LOGIN_CODE не задан. Укажи код из Telegram в переменных окружения и перезапусти.")
            return False

        # Пытаемся войти с кодом
        logger.info("🔑 Авторизуюсь с кодом из переменных окружения...")
        await app.sign_in(PHONE_NUMBER, sent.phone_code_hash, LOGIN_CODE)
        logger.info("✅ Авторизация успешна, сессия сохранена!")
        return True

    except SessionPasswordNeeded:
        logger.error("❌ У аккаунта включён пароль 2FA, добавь поддержку PASSWORD в config.py.")
        return False
    except PhoneCodeInvalid:
        logger.error("❌ Неверный код авторизации. Проверь LOGIN_CODE.")
        return False
    except PhoneCodeExpired:
        logger.error("❌ Код авторизации истёк. Получи новый и перезапусти контейнер.")
        return False
    except Exception as e:
        logger.exception(f"💥 Ошибка при авторизации: {e}")
        return False


async def check_authorization_status(app: Client):
    """
    Проверяет, авторизован ли клиент.
    """
    try:
        me = await app.get_me()
        if me:
            logger.info(f"✅ Клиент уже авторизован: {me.first_name} (@{me.username})")
            return True
        return False
    except Exception:
        return False
