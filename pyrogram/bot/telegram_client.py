"""
telegram_client.py — основной код, работающий после входа в Telegram
"""
import logging
from pyrogram import Client, filters


async def run_telegram_client(app: Client):
    """
    Регистрирует хендлеры и запускает работу userbota
    """

    @app.on_message(filters.command("ping"))
    async def ping(_, message):
        await message.reply("🏓 Pong!")

    @app.on_message(filters.command("me"))
    async def me_cmd(_, message):
        user = await app.get_me()
        await message.reply(f"👤 {user.first_name} (@{user.username})")

    logging.info("⚡ Userbot слушает Telegram...")
    await idle_forever()


async def idle_forever():
    """
    Зависает, пока не остановят контейнер / процесс
    """
    import asyncio
    while True:
        await asyncio.sleep(3600)
