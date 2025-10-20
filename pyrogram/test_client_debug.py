# test_client_manual_fixed.py
import logging
import os
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

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
print("[INFO] Создаём клиента Pyrogram...")

app = Client(
    name=SESSION_PATH,
    api_id=API_ID,
    api_hash=API_HASH,
)

print("[INFO] Запускаем ручную авторизацию...")

try:
    app.connect()

    # Проверяем: если не авторизован — проходим логин
    authorized = False
    try:
        me = app.get_me()
        authorized = True
        print(f"[INFO] Уже авторизован как {me.first_name}")
    except Exception:
        print("[ACTION] Сессия невалидна — начинаем ручной вход...")

    if not authorized:
        sent_code = app.send_code(PHONE_NUMBER)
        code = input("[INPUT] Введите код подтверждения из Telegram: ").strip()

        try:
            app.sign_in(PHONE_NUMBER, code)
        except SessionPasswordNeeded:
            password = input("[INPUT] Введите пароль 2FA: ").strip()
            app.check_password(password)

        me = app.get_me()
        print(f"[SUCCESS] Вошли как {me.first_name} (@{me.username})")

finally:
    app.disconnect()
    print("[INFO] Клиент завершил работу.")
