# userbot/core/telegram_client.py

"""
Модуль для инициализации Telegram клиента
Создает и настраивает подключение к Telegram API
"""
import logging
import os
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, SessionExpired, SessionPasswordNeeded
from config import API_ID, API_HASH, SESSION_PATH
from .auth_handler import authorize_with_code, check_authorization_status # Используем наш auth_handler

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра клиента (опционально)
_client_instance = None


def create_client() -> Client:
    """
    Создает и возвращает Pyrogram клиент
    """
    global _client_instance
    try:
        # Pyrogram по умолчанию читает API_ID и API_HASH из переменных окружения,
        # но мы используем явное объявление, как в вашем коде Telethon.
        if not API_ID or not API_HASH:
            raise ValueError("Не найдены переменные окружения API_ID или API_HASH.")
        
        # В Pyrogram SESSION_PATH - это префикс для имени файла сессии.
        api_id = int(API_ID)
        
        client = Client(
            name=SESSION_PATH,      # Имя сессии (будет файлом .session)
            api_id=api_id,
            api_hash=API_HASH
        )
        _client_instance = client
        return client
        
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.error("➡️ Пожалуйста, убедитесь, что API_ID является числом, и обе переменные установлены.")
        raise


def get_client() -> Client:
    """
    Возвращает ранее созданный экземпляр клиента
    """
    if _client_instance is None:
         logger.error("❌ Клиент не инициализирован. Вызовите create_client() сначала.")
         raise RuntimeError("Клиент Pyrogram не инициализирован.")
    return _client_instance

async def initialize_client(client: Client) -> bool:
    """
    Инициализирует клиент и проверяет/выполняет авторизацию.
    В Pyrogram client.start() - это асинхронный контекстный менеджер,
    который выполняет подключение и авторизацию.
    """
    
    # Пытаемся запустить клиент. Pyrogram сам обработает авторизацию
    # (запрос кода, пароля) если сессия отсутствует или истекла.
    try:
        # client.start() выполняет connect() и проверку авторизации
        await client.start() 
        logger.info("✅ Клиент Pyrogram запущен (подключен).")

    except SessionExpired:
        logger.warning("⚠️ Сессия истекла. Требуется повторная авторизация. Удалите файл сессии и запустите снова.")
        return False
    except SessionPasswordNeeded:
        # Если нужна 2FA, клиент выведет запрос в консоль, если это первый запуск.
        # Если это не первый запуск, то нужно использовать client.log_in() с паролем.
        logger.info("🔐 Требуется двухфакторная аутентификация (2FA).")
        # Для простоты здесь предполагаем, что Pyrogram сам обработает ввод.
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске клиента: {e}")
        return False
        
    
    # Проверяем статус авторизации (для надежности)
    me = await client.get_me()
    
    if me:
        user_info = f"{me.first_name or ''} (@{me.username})" if me.username else f"{me.first_name or ''}"
        logger.info(f"✅ Успешная авторизация под аккаунтом: {user_info.strip()}")
        return True
    else:
        logger.error("❌ Не удалось получить информацию о пользователе. Авторизация не удалась.")
        await client.stop()
        return False