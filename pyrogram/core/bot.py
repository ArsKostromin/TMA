import asyncio
import logging
from core.auth.telegram_client import initialize_client

logger = logging.getLogger(__name__)

async def main_userbot():
    logger.info("🚀 Запуск Pyrogram Userbot...")

    app = await initialize_client()
    if not app:
        logger.error("❌ Не удалось инициализировать Pyrogram-клиент.")
        return

    async with app:
        me = await app.get_me()
        logger.info(f"👤 Авторизован как {me.first_name} (@{me.username})")
        logger.info("💫 Userbot готов к работе!")

        # Здесь твоя логика: слушай чаты, пересылай подарки и т.д.
        await asyncio.Event().wait()
