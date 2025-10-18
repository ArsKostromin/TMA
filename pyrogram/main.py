"""
Главная точка входа для Pyrogram Userbot
Запускает инициализацию и работу userbot'а (однократный запуск)
"""

import asyncio
import logging
import signal
import sys
from core.bot import main_userbot

# --- Настройка логов ---
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("pyrogram-main")


# --- Грейсфул-шатдаун для Docker / Ctrl+C ---
def handle_sigterm(*_):
    logger.warning("🛑 Получен сигнал остановки (SIGTERM). Завершаю работу...")
    sys.exit(0)


async def main():
    """
    Главная точка входа
    """
    logger.info("🚀 Запуск Pyrogram Userbot...")

    # Добавляем обработку сигналов
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_sigterm)
        except NotImplementedError:
            pass  # Windows, не ругайся

    # Просто запускаем один раз и ждём
    try:
        await main_userbot()
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка в userbot: {e}")
    finally:
        logger.info("👋 Работа userbot завершена.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Работа завершена пользователем.")
