import logging
import asyncio
import sys

# Импортируем наш конфиг
try:
    import config
except ImportError:
    print("Ошибка: не найден файл config.py. Убедитесь, что он существует.")
    sys.exit(1)

# Импортируем функции из новой папки auth
from .auth.telegram_client import create_client
from .auth.auth_handler import run_client
from .gift_listener.gifts_listener import register_gift_listener, process_chat_history

# Настройка логирования
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger("pyrogram-main")


async def main_userbot():
    """
    Главная асинхронная функция, которую запускает main.py
    Инициализирует клиента и запускает цикл авторизации/работы.
    """
    try:
        # 1. Создаем объект клиента
        app = create_client(config)
        logger.info(config)

        # 2. Запускаем клиента
        await app.start()
        logger.info("🚀 Pyrogram Userbot запущен успешно!")

        # 3. 🎁 Регистрируем обработчик новых гифтов
        register_gift_listener(app)
        logger.info("🎁 Обработчик новых гифтов зарегистрирован!")

        # 4. 📜 Сканируем историю на предмет непрочитанных гифтов
        logger.info("📜 Начинаю сканирование истории на предмет непрочитанных гифтов...")
        await process_chat_history(app)
        logger.info("📜 Сканирование истории завершено!")

        # 5. После обработки — продолжаем обычную работу
        await run_client(app)

    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в userbot: {e}", exc_info=True)
    finally:
        # Закрываем соединение при завершении
        try:
            await app.stop()
        except Exception:
            pass
        logger.info("👋 Работа userbot завершена.")


if __name__ == "__main__":
    try:
        asyncio.run(main_userbot())
    except KeyboardInterrupt:
        logger.info("Получен сигнал (Ctrl+C). Завершение работы...")
