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
logger = logging.getLogger("pyrogram-main")

# --- Обработка сигнала SIGTERM / SIGINT ---
def handle_sigterm(*_):
    logger.warning("🛑 Получен сигнал остановки (SIGTERM). Завершаю работу...")
    sys.exit(0)


async def run_userbot():
    """
    Обёртка, запускающая userbot и отлавливающая ошибки
    """
    try:
        await main_userbot()
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка в userbot: {e}")
        await asyncio.sleep(5)


async def main():
    """
    Главная корутина — точка входа
    """
    logger.info("🚀 Запуск Pyrogram Userbot...")

    # Добавляем обработку сигналов для Docker
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_sigterm)
        except NotImplementedError:
            # Windows не умеет add_signal_handler, поэтому молчим
            pass

    # Основной цикл перезапуска
    while True:
        await run_userbot()
        logger.warning("🔁 Перезапуск userbot через 5 секунд...")
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Работа завершена пользователем.")
