import logging
import os
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeRequired

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SESSION_PATH = "session/test_userbot"

app = Client(
    name=SESSION_PATH,
    api_id=API_ID,
    api_hash=API_HASH,
)

try:
    app.connect()  # подключаемся к Telegram

    try:
        # Пытаемся войти вручную
        app.send_code_request(PHONE_NUMBER)
        code = input("Введите код подтверждения из Telegram: ")
        app.sign_in(PHONE_NUMBER, code)
    except SessionPasswordNeeded:
        # если включена 2FA
        password = input("Введите пароль 2FA: ")
        app.check_password(password)

    me = app.get_me()
    print(f"[INFO] Вы вошли как: {me.first_name} (@{me.username})")

finally:
    app.disconnect()
    print("[INFO] Клиент завершил работу.")
