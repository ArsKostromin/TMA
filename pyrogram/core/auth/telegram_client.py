import logging
import os
import sqlite3  # <-- вот его и не хватало
from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    FloodWait,
    BadRequest
)
from config import API_ID, API_HASH, PHONE_NUMBER, LOGIN_CODE, SESSION_PATH

logger = logging.getLogger(__name__)


async def initialize_client():
    """
    Полностью автоматическая авторизация Pyrogram без input().
    Все данные берутся из config.py / .env
    """
    app = None
    try:
        logger.info("🚀 Инициализация Pyrogram клиента...")

        # создаём клиент
        session_name = SESSION_PATH.replace(".session", "")
        session_dir = os.path.dirname(SESSION_PATH) or "."

        # убедимся что директория для сессии существует
        os.makedirs(session_dir, exist_ok=True)

        app = Client(
            name=session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=session_dir
        )

        # пробуем подключиться
        await app.connect()

        # если уже авторизован
        try:
            me = await app.get_me()
            if me:
                logger.info(f"✅ Уже авторизован как {me.first_name} (@{me.username})")
                return app
        except Exception:
            pass

        # если нет авторизации — авторизуемся через код
        if not PHONE_NUMBER:
            raise ValueError("❌ PHONE_NUMBER не указан в переменных окружения")

        logger.info(f"📱 Отправляю код на {PHONE_NUMBER}...")
        sent = await app.send_code(PHONE_NUMBER)

        if not LOGIN_CODE:
            raise ValueError("❌ LOGIN_CODE не задан. Добавь его в .env и перезапусти контейнер")

        logger.info("🔑 Пробую войти с LOGIN_CODE из конфига...")
        await app.sign_in(PHONE_NUMBER, sent.phone_code_hash, LOGIN_CODE)
        logger.info("✅ Авторизация прошла успешно, сессия сохранена!")

        return app

    except PhoneCodeInvalid:
        logger.error("❌ Неверный код авторизации. Проверь LOGIN_CODE.")
    except PhoneCodeExpired:
        logger.error("❌ Код авторизации истёк. Получи новый и перезапусти.")
    except SessionPasswordNeeded:
        logger.error("❌ Включена 2FA. Добавь парольную авторизацию (ещё не реализовано).")
    except FloodWait as e:
        logger.error(f"⏳ Telegram просит подождать {e.value} секунд.")
    except BadRequest as e:
        logger.error(f"🚫 Telegram отказал: {e}")
    except sqlite3.OperationalError as e:
        logger.error(f"📁 Ошибка доступа к файлу сессии: {e}")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в userbot: {e}")
    finally:
        if app:
            try:
                await app.disconnect()
            except Exception:
                pass

    return None
