import asyncio
import logging
import threading
import uvicorn
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
# from api.server import app
from core.bot import main_userbot

# Настройка логов
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL), datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# def run_fastapi():
#     """Запускает веб-сервер Uvicorn (FastAPI) в отдельном потоке."""
#     # Используем reload=False, так как это запускается внутри потока
#     uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

if __name__ == "__main__":
    logger.info("🤖 Запуск Userbot и FastAPI сервера...")
    
    # # Запуск FastAPI в отдельном потоке (threading)
    # server_thread = threading.Thread(target=run_fastapi, daemon=True)
    # server_thread.start()
    # logger.info("🌐 FastAPI запущен на 0.0.0.0:8080 в фоновом потоке.")

    # Запуск userbot'а в основном потоке (asyncio)
    try:
        asyncio.run(main_userbot())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал KeyboardInterrupt. Завершение работы.")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в основном цикле asyncio: {e}")
