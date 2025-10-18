import asyncio
import logging
# Удаляем импорты threading, uvicorn и api.server, так как они больше не нужны.
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from core.bot import main_userbot

# Настройка логов
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL), datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# Функция run_fastapi удалена, так как веб-сервер больше не запускается.

if __name__ == "__main__":
    logger.info("🚀 Приложение запущено. Начинаю запуск Userbot.")
    
    # 1. Удален запуск FastAPI в отдельном потоке.

    # 2. Запуск userbot'а в основном потоке (asyncio).
    # main_userbot блокирует основной поток, пока не завершит работу.
    try:
        asyncio.run(main_userbot())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал прерывания (Ctrl+C). Завершение работы.")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в основном цикле asyncio: {e}")
    finally:
        logger.info("😴 Завершение работы Userbot.")
