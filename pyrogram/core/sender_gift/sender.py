import logging
import asyncio
from pyrogram import Client
from pyrogram.errors import RPCError, StargiftUsageLimited

logger = logging.getLogger("pyrogram-main.sender")



async def send_gift_to_user(app: Client, recipient_id: int | str, owned_gift_id: str):
    """
    Отправляем коллекционный подарок (TON NFT gift) пользователю через transfer_gift().
    """
    try:
        logger.info(f"🎁 Пытаемся передать коллекционный подарок {owned_gift_id} пользователю {recipient_id}...")

        # Отправляем подарок
        result = await app.transfer_gift(
            owned_gift_id=owned_gift_id,
            new_owner_chat_id=recipient_id
        )

        logger.info(f"✅ Успешно передан подарок {owned_gift_id} пользователю {recipient_id}")
        logger.debug(f"Ответ Kurigram API: {result}")

    except RPCError as e:
        logger.error(f"❌ RPC ошибка при передаче подарка: {e}")
    except Exception as e:
        logger.error(f"💥 Непредвиденная ошибка при передаче подарка: {e}", exc_info=True)


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
