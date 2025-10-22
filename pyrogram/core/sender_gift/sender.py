import logging
import asyncio
from pyrogram import Client
from pyrogram.errors import RPCError, StargiftUsageLimited

logger = logging.getLogger("pyrogram-main.sender")


async def send_gift_to_user(app: Client, peer_id: int, gift_id: int):
    """
    Отправляет подарок (NFT) пользователю через Pyrogram метод send_gift.

    :param app: Инициализированный клиент Pyrogram
    :param peer_id: Telegram ID получателя
    :param gift_id: ID подарка (NFT)
    :return: True, если отправлено успешно, иначе False
    """
    try:
        logger.info(f"🎁 Отправляем подарок ID={gift_id} пользователю ID={peer_id}...")

        # Проверяем баланс перед отправкой
        balance = await app.get_stars_balance()
        logger.info(f"💰 Текущий баланс: {balance}")

        if balance <= 0:
            logger.error("❌ Недостаточно звёзд для отправки подарка")
            return False

        # Отправляем подарок через API Pyrogram
        result = await app.send_gift(
            chat_id=peer_id,
            gift_id=gift_id,
            is_private=True,
        )

        logger.info(f"✅ Подарок успешно отправлен пользователю {peer_id}! Ответ API: {result}")
        return True

    except StargiftUsageLimited:
        logger.warning(f"⚠️ Саплай подарка ID={gift_id} закончился")
        return False

    except RPCError as e:
        logger.error(f"❌ Ошибка RPC при отправке подарка: {e}")
        return False

    except Exception as e:
        logger.error(f"💥 Непредвиденная ошибка при отправке подарка: {e}", exc_info=True)
        return False


async def show_my_gifts(app: Client):
    """
    Получаем все подарки (включая коллекционные) пользователя и выводим их в лог.
    Используется Kurigram API method get_chat_gifts().
    """
    try:
        logger.info("📦 Получаем все подарки через Kurigram API…")

        # получаем генератор подарков
        gifts_gen = app.get_chat_gifts(chat_id="me")  # или user_id
        found = False

        async for gift in gifts_gen:
            found = True
            # предполагаем, что объект gift имеет поля id, name/title, price или cost, owner_id, rarity и т.д.
            gift_id = getattr(gift, "id", None)
            name = getattr(gift, "name", getattr(gift, "title", "Неизвестно"))
            price = getattr(gift, "price", None)
            owner = getattr(gift, "owner_id", None)
            logger.info(f"🎁 Подарок: {name} | ID={gift_id} | Цена: {price} звёзд | Владелец: {owner}")

        if not found:
            logger.info("⚠️ У тебя нет подарков (или не удалось получить список).")

    except Exception as e:
        logger.error(f"💥 Ошибка при получении коллекционных подарков: {e}", exc_info=True)
