"""
Главная точка входа для Pyrogram Userbot
Запускает инициализацию и работу userbot'а
"""

import asyncio
import logging
import os
import signal
import sys
from core.bot import main_userbot

# --- Настройка логов ---
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Грейсфул-шатдаун для Docker ---
def handle_sigterm(*_):
    logger.warning("🛑 Получен сигнал остановки (SIGTERM). Завершаю работу...")
    sys.exit(0)


async def run_userbot():
    """
    Запуск userbot с защитой от крэшей
    """
    try:
        await main_userbot()
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка в userbot: {e}")
        await asyncio.sleep(5)


async def main():
    """
    Главная точка входа
    """
    logger.info("🚀 Запуск Pyrogram Userbot...")

    # Обработка сигналов для Docker
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_sigterm)
        except NotImplementedError:
            # Windows не поддерживает add_signal_handler
            pass

    # Основной цикл — бот сам перезапускается при вылете
    while True:
        await run_userbot()
        logger.warning("🔁 Перезапуск userbot через 5 секунд...")
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Работа завершена пользователем.")
