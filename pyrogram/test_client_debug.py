# test_client_manual_fixed.py
import logging
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
import config  # ✅ импортируем твой конфиг, лежит рядом

# -----------------------------
# 🔥 Настраиваем логирование
# -----------------------------
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger("userbot")

# -----------------------------
# 📦 Достаём конфиг
# -----------------------------
API_ID = int(config.API_ID)
API_HASH = config.API_HASH
PHONE_NUMBER = config.PHONE_NUMBER
SESSION_PATH = config.SESSION_PATH

logger.info(f"API_ID={API_ID}, PHONE={PHONE_NUMBER}")
logger.info("Создаём клиент Pyrogram...")

# -----------------------------
# 🚀 Инициализация клиента
# -----------------------------
app = Client(
    name=SESSION_PATH,
    api_id=API_ID,
    api_hash=API_HASH
)

# -----------------------------
# 🔐 Авторизация
# -----------------------------
logger.info("Запускаем ручную авторизацию...")

try:
    app.connect()

    authorized = False
    try:
        me = app.get_me()
        authorized = True
        logger.info(f"Уже авторизован как {me.first_name} (@{me.username})")
    except Exception:
        logger.warning("Сессия невалидна — начинаем ручной вход...")

    if not authorized:
        sent_code = app.send_code(PHONE_NUMBER)
        phone_code_hash = sent_code.phone_code_hash
        logger.info(f"Код отправлен на {PHONE_NUMBER}")

        code = input("[INPUT] Введите код подтверждения из Telegram: ").strip()

        try:
            app.sign_in(
                phone_number=PHONE_NUMBER,
                phone_code_hash=phone_code_hash,
                phone_code=code
            )
        except SessionPasswordNeeded:
            password = input("[INPUT] Введите пароль 2FA: ").strip()
            app.check_password(password)

        me = app.get_me()
        logger.info(f"[SUCCESS] Вошли как {me.first_name} (@{me.username})")

except Exception as e:
    logger.error(f"Критическая ошибка авторизации: {e}", exc_info=True)
finally:
    app.disconnect()
    logger.info("Клиент завершил работу.")
