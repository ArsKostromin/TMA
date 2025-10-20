# test_client_manual_code.py
import logging
import os
from pyrogram import Client

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SESSION_PATH = "session/test_userbot"

print(f"[INFO] API_ID={API_ID}, PHONE={PHONE_NUMBER}")

app = Client(
    name=SESSION_PATH,
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

print("[INFO] Ручной вход в аккаунт...")

try:
    # ручной старт
    app.connect()
    
    if not app.is_user_authorized():
        # введи код, который пришёл в Telegram
        code = input("Введите код подтверждения: ")
        app.sign_in(phone_number=PHONE_NUMBER, code=code)

    print("[INFO] Клиент авторизован, можно работать с Pyrogram!")

    # Пример: получить свои данные
    me = app.get_me()
    print(f"[INFO] Вы вошли как: {me.first_name} (@{me.username})")

finally:
    app.disconnect()
    print("[INFO] Клиент завершил работу.")
