import logging
import asyncio
import sys

# === Импорт конфигурации ===
try:
    import config
except ImportError:
    print("❌ Ошибка: не найден файл config.py. Убедитесь, что он существует.")
    sys.exit(1)

# === Импорт компонентов ===
from .auth.telegram_client import create_client
from .auth.auth_handler import run_client
from .gift_listener.gifts_listener import register_gift_listener, process_chat_history
from .sender_gift.sender import send_gift_to_user, show_my_gifts

# === Настройка логирования ===
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger("pyrogram-main")


async def main_userbot():
    """
    Главная асинхронная функция, инициализирующая Pyrogram userbot.
    Управляет запуском клиента, авторизацией и обработкой логики отправки подарков.
    """
    app = None
    try:
        # 1️⃣ Создаём клиент Telegram
        app = create_client(config)
        logger.info("⚙️ Конфиг успешно загружен и клиент создан.")

        # 2️⃣ Запускаем клиента
        await app.start()
        me = await app.get_me()
        logger.info(f"🚀 Userbot запущен как {me.first_name} (@{me.username}) | ID={me.id}")

        await show_my_gifts(app)

        # # === Пример ручной отправки подарка ===
        # peer_id = 1207534564      # ID получателя
        # gift_id = 5852757491946882427  # ID подарка (NFT)
        # logger.info(f"🎁 Попытка отправки подарка {gift_id} пользователю {peer_id}...")

        # success = await send_gift_to_user(app, peer_id, gift_id)

        # if success:
        #     logger.info(f"✅ Подарок {gift_id} успешно отправлен пользователю {peer_id}.")
        # else:
        #     logger.warning(f"⚠️ Не удалось отправить подарок {gift_id} пользователю {peer_id}.")

        # === Пример регистрации слушателя подарков (если понадобится) ===
        # register_gift_listener(app)
        # logger.info("🎁 Обработчик новых подарков зарегистрирован.")

        # === Пример сканирования истории (если нужно включить) ===
        # logger.info("📜 Сканирую историю на предмет непрочитанных подарков...")
        # await process_chat_history(app)
        # logger.info("📜 Сканирование завершено.")

        # 3️⃣ Запускаем клиент в режиме ожидания событий
        logger.info("🕓 Ожидание событий... (Ctrl+C для выхода)")
        await run_client(app)

    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в userbot: {e}", exc_info=True)
    finally:
        # 4️⃣ Корректное завершение работы
        if app and app.is_connected:
            await app.stop()
        logger.info("👋 Работа userbot завершена.")