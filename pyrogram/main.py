import asyncio
import logging
# Удалены импорты threading, uvicorn и api.server.
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from bot import main_userbot  # Изменено: core.bot -> bot

# Настройка логов
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL), datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Приложение запущено. Начинаю запуск Userbot.")
    
    # Запуск userbot'а в основном асинхронном потоке.
    try:
        asyncio.run(main_userbot())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал прерывания (Ctrl+C). Завершение работы.")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в основном цикле asyncio: {e}")
    finally:
        logger.info("😴 Завершение работы Userbot.")
