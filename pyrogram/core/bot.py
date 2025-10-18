"""
Главный модуль логики Userbot'а
Здесь происходит запуск, инициализация и постоянная работа клиента Pyrogram
"""

import asyncio
import logging
from pyrogram import idle
from .auth.telegram_client import create_client, initialize_client

logger = logging.getLogger(__name__)


async def main_userbot():
    """
    Главная точка входа в userbot
    """
    app = create_client()

    try:
        logger.info("🚀 Инициализация Pyrogram клиента...")
        ok = await initialize_client(app)
        if not ok:
            logger.error("❌ Не удалось авторизовать клиента. Завершаю работу.")
            return

        # Старт клиента
        await app.start()

        me = await app.get_me()
        logger.info(f"✅ Бот запущен под аккаунтом: {me.first_name} (@{me.username})")

        # --- Твои обработчики событий можно подключать тут ---
        # пример:
        # from .handlers import register_handlers
        # register_handlers(app)

        logger.info("💫 Userbot запущен. Ожидаю события...")
        await idle()  # Держит клиент живым, пока не остановят вручную

    except Exception as e:
        logger.exception(f"💥 Ошибка в работе Userbot: {e}")

    finally:
        # Завершаем соединение корректно
        try:
            await app.stop()
        except Exception:
            pass
        logger.info("🧹 Клиент остановлен.")
        await asyncio.sleep(2)
