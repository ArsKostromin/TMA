# Файл: pyrogram/core/auth/auth_handler.py

import logging
from pyrogram import Client, idle
from pyrogram.errors import SessionPasswordNeeded, FloodWait

# Логгер, который будет использоваться
logger = logging.getLogger("pyrogram-main")

async def run_client(app: Client):
    """
    Запускает, мониторит и корректно останавливает Pyrogram Client.
    """
    logger.info("Попытка запуска клиента и авторизации...")
    
    # **ПРИ ПЕРВОМ ЗАПУСКЕ:**
    # Именно здесь, внутри `await app.start()`, Pyrogram остановится
    # и запросит код авторизации/2FA пароль в консоли.

    try:
        await app.start()
        
        me = await app.get_me()
        logger.info(f"✅ Успешный вход как: {me.first_name} (@{me.username})")
        
        # Опционально: Отправка тестового сообщения
        # await app.send_message("me", f"✅ Юзербот на Pyrogram успешно запущен!\nВход от: {me.first_name}")
        
        logger.info("Клиент запущен и работает. (Ожидание команды остановки...)")
        
        # Эта команда не дает скрипту завершиться
        await idle() 
        
    except SessionPasswordNeeded:
        logger.error("Обнаружена двухфакторная аутентификация (2FA).")
        logger.error("Пожалуйста, запустите скрипт еще раз и введите 2FA пароль, когда его попросят.")
        
    except FloodWait as e:
        logger.error(f"❌ ОШИБКА TELEGRAM (FloodWait): Слишком много попыток входа.")
        logger.error(f"Тебе нужно подождать {e.value} секунд ({round(e.value / 3600, 1)} часов), прежде чем пробовать снова.")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при работе клиента: {e}")
        
    finally:
        if app.is_connected:
            await app.stop()
            logger.info("👋 Клиент Pyrogram корректно остановлен.")