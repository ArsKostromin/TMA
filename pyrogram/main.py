"""
Главная точка входа для Pyrogram UserBot
Инициализирует клиента, проходит авторизацию и запускает вспомогательные модули
"""
import asyncio
import logging
from pyrogram import Client
from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_PATH, LOGIN_CODE
from core.auth_handler import ensure_login
from core.telegram_client import run_telegram_client


# --- Логирование ---
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)


async def main():
    logging.info("🚀 Запуск Pyrogram Userbot...")

    # Инициализация клиента
    app = Client(
        SESSION_PATH,
        api_id=API_ID,
        api_hash=API_HASH
    )

    # --- Авторизация ---
    await ensure_login(app, PHONE_NUMBER, LOGIN_CODE)

    # --- Подключение клиента ---
    async with app:
        logging.info("✅ Userbot успешно вошёл в Telegram.")
        await run_telegram_client(app)

    logging.info("🛑 Работа Pyrogram завершена.")


if __name__ == "__main__":
    asyncio.run(main())
