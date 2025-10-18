# Файл: pyrogram/core/bot.py (ОБНОВЛЕННЫЙ)

import logging
import asyncio
import sys

# Импортируем наш конфиг
try:
    import config
except ImportError:
    print("Ошибка: не найден файл config.py. Убедитесь, что он существует.")
    sys.exit(1)

# Импортируем функции из новой папки auth
from .auth.telegram_client import create_client
from .auth.auth_handler import run_client

# Настройка логирования
logging.basicConfig(level=config.LOG_LEVEL, 
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", 
                    datefmt=config.LOG_DATE_FORMAT)
# Задаем имя логгера, которое будем использовать во всех модулях
logger = logging.getLogger("pyrogram-main")


async def main_userbot():
    """
    Главная асинхронная функция, которую запускает main.py
    Инициализирует клиента и запускает цикл авторизации/работы.
    """
    try:
        # 1. Создаем объект клиента
        app = create_client(config)
        
        # 2. Запускаем авторизацию и работу
        await run_client(app)
        
    except ValueError as e:
        # Ошибка, пойманная в create_client (нет API_ID/PHONE_NUMBER)
        logger.error(f"❌ Ошибка конфигурации: {e}")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в цикле userbot: {e}")
    finally:
        logger.info("👋 Работа userbot завершена.")


if __name__ == "__main__":
    # Локальный запуск (если ты запускаешь pyrogram/core/bot.py напрямую)
    try:
        # Запускаем `main_userbot()` в асинхронном цикле
        asyncio.run(main_userbot())
    except KeyboardInterrupt:
        logger.info("Получен сигнал (Ctrl+C). Завершение работы...")