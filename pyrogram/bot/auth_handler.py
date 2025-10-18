"""
auth_handler.py — модуль авторизации Pyrogram-клиента
Если сессия отсутствует — проходит логин через телефон и код
"""
import asyncio
import logging
from pyrogram.errors import SessionPasswordNeeded


async def ensure_login(app, phone_number: str, code: str | None = None):
    """
    Проверяет логин и, если нужно, проходит авторизацию
    """
    if await app.connect():
        try:
            me = await app.get_me()
            logging.info(f"👤 Уже авторизован как {me.first_name} (@{me.username})")
            return
        except Exception:
            pass  # не залогинен — продолжаем

    logging.info("📱 Авторизация через Pyrogram...")

    sent = await app.send_code(phone_number)
    if not code:
        code = input("🔑 Введи код из Telegram: ")

    try:
        await app.sign_in(phone_number, sent.phone_code_hash, code)
    except SessionPasswordNeeded:
        pw = input("🔐 Введи пароль 2FA: ")
        await app.check_password(pw)

    me = await app.get_me()
    logging.info(f"✅ Вход выполнен как {me.first_name} (@{me.username})")
    await app.disconnect()
