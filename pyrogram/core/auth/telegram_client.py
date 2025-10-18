# Файл: pyrogram/core/auth/telegram_client.py

import logging
from pyrogram import Client

# Логгер, который будет использоваться
logger = logging.getLogger("pyrogram-main")

# Глобальная переменная для клиента (опционально, но удобно)
app: Client = None

def create_client(config):
    """
    Создает и возвращает объект Pyrogram Client, используя данные из конфига.
    """
    global app

    # Проверка обязательных переменных
    if not config.API_ID or not config.API_HASH:
        logger.error("API_ID и API_HASH должны быть установлены в переменных окружения.")
        raise ValueError("API credentials missing.")
        
    if not config.PHONE_NUMBER:
        logger.error("PHONE_NUMBER должен быть установлен в переменных окружения.")
        raise ValueError("Phone number missing.")

    logger.info("Инициализация клиента Pyrogram...")

    # 'name' - это путь к файлу сессии (без .session)
    app = Client(
        name=config.SESSION_PATH,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        phone_number=config.PHONE_NUMBER  # Указываем номер телефона сразу
    )
    return app