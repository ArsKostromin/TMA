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
from .sender_gift.sender import send_gift_to_user  # 👈 добавили импорт

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

        # 2. Запускаем клиента
        await app.start()
        logger.info("🚀 Pyrogram Userbot запущен успешно!")

        # 3. 🎁 Отправляем подарок при старте
        peer_id = 1207534564  # ID получателя (jhgvcbcg)
        gift_id = 5852757491946882427  # ID гифта SnakeBox-29826

        logger.info("🎁 Пытаемся отправить подарок при старте...")
        await send_gift_to_user(app, peer_id, gift_id)

        # 4. После отправки — продолжаем обычную работу
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
