# test_client_debug.py
import logging
import os
from pyrogram import Client

# 🔥 Включаем максимально подробный лог
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG = максимум инфы
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Берём переменные окружения
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
    phone_number=PHONE_NUMBER
)

print("[INFO] Запускаем клиент (app.run())...")

try:
    # run() = start + idle + stop
    app.run()
except Exception as e:
    print(f"[ERROR] Критическая ошибка при запуске клиента: {e}")
finally:
    print("[INFO] Клиент завершил работу.")
