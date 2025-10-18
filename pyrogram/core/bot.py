import logging
import asyncio
from pyrogram import Client, idle
from pyrogram.errors import SessionPasswordNeeded

# Импортируем ваш конфиг
try:
    import config
except ImportError:
    print("Ошибка: не найден файл config.py. Убедитесь, что он существует.")
    exit(1)

# Настройка логирования из вашего конфига
logging.basicConfig(level=config.LOG_LEVEL, 
                    format=config.LOG_FORMAT, 
                    datefmt=config.LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# Проверка обязательных переменных
if not config.API_ID or not config.API_HASH:
    logger.error("API_ID и API_HASH должны быть установлены в переменных окружения.")
    exit(1)
    
if not config.PHONE_NUMBER:
    logger.error("PHONE_NUMBER должен быть установлен в переменных окружения.")
    exit(1)

logger.info("Инициализация клиента Pyrogram...")

# 'name' - это путь к файлу сессии (без .session)
# Мы берем все данные из вашего config.py
app = Client(
    name=config.SESSION_PATH,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    phone_number=config.PHONE_NUMBER  # Указываем номер телефона сразу
)

async def main():
    """
    Основная асинхронная функция для запуска клиента
    """
    global app
    logger.info("Попытка запуска клиента...")
    try:
        await app.start()
        
        # ---------------------------------------------------------------------
        # **ПРИ ПЕРВОМ ЗАПУСКЕ:**
        # Именно здесь, внутри `await app.start()`, Pyrogram остановится
        # и напишет в консоль "Enter code: ".
        # Вы должны будете ввести код.
        # Переменная `LOGIN_CODE` из конфига здесь НЕ используется.
        # ---------------------------------------------------------------------

        me = await app.get_me()
        logger.info(f"Успешный вход как: {me.first_name} (@{me.username})")
        
        # Отправляем сообщение в "Избранное" (себе), чтобы проверить, что все работает
        await app.send_message("me", f"✅ Юзербот на Pyrogram успешно запущен!\nВход от: {me.first_name}")
        
        logger.info("Клиент запущен и работает. Нажмите Ctrl+C для остановки.")
        
        # Эта команда не дает скрипту завершиться, 
        # позволяя ему продолжать работать и слушать обновления.
        await idle() 
        
    except SessionPasswordNeeded:
        logger.error("Обнаружена двухфакторная аутентификация (2FA).")
        logger.error("Пожалуйста, запустите скрипт еще раз и введите 2FA пароль, когда его попросят.")
        # Pyrogram запросит пароль при следующем `app.start()`
    except Exception as e:
        logger.error(f"Произошла критическая ошибка: {e}")
    finally:
        if app.is_connected:
            await app.stop()
            logger.info("Клиент корректно остановлен.")

if __name__ == "__main__":
    # `app.run(main())` - это удобный способ, который запускает `main()`,
    # обрабатывает `asyncio`, `start()`, `idle()` и `stop()` за вас.
    try:
        app.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал (Ctrl+C). Завершение работы...")