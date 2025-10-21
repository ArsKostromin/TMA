# Файл: pyrogram/core/auth/auth_handler.py

import logging
from pyrogram import Client, idle
from pyrogram.errors import SessionPasswordNeeded, FloodWait

logger = logging.getLogger("pyrogram-main")

async def run_client(app: Client):
    """
    Управляет активным клиентом Pyrogram — ожидает события и корректно завершает работу.
    Клиент должен быть уже запущен (app.start() выполнен ранее).
    """
    try:
        # Проверяем, что клиент действительно запущен
        if not app.is_connected:
            logger.warning("⚠️ Клиент не был запущен — выполняю app.start() вручную.")
            await app.start()

        me = await app.get_me()
        logger.info(f"✅ Pyrogram запущен как: {me.first_name} (@{me.username})")

        # Блокируем поток до сигнала остановки (Ctrl+C или disconnect)
        logger.info("🕓 Ожидание событий... (Ctrl+C для выхода)")
        await idle()

    except SessionPasswordNeeded:
        logger.error("❌ Обнаружена двухфакторная аутентификация (2FA). Введите пароль вручную.")
    except FloodWait as e:
        logger.error(f"💀 FloodWait: слишком много запросов. Жди {e.value} сек ({round(e.value / 3600, 1)} ч).")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при работе клиента: {e}", exc_info=True)
    finally:
        if app.is_connected:
            await app.stop()
            logger.info("👋 Клиент Pyrogram корректно остановлен.")
