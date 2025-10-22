import logging
import asyncio
from pyrogram import Client
from pyrogram.errors import RPCError, StargiftUsageLimited

logger = logging.getLogger("pyrogram-main.sender")


async def send_gift_to_user(app: Client, recipient_id: int, gift_id: int, slug: str):
    """
    Отправляем коллекционный подарок (TON NFT gift) пользователю.
    """
    try:
        logger.info(f"🎁 Отправляем коллекционный подарок {slug} (ID={gift_id}) пользователю {recipient_id}...")

        result = await app.send_upgraded_gift(
            peer_id=recipient_id,
            gift_id=gift_id,
            slug=slug,  # slug = символ подарка, например SnakeBox-29826
            is_private=False  # если True — не будет видно в профиле
        )

        logger.info(f"✅ Подарок {slug} успешно отправлен пользователю {recipient_id}!")
        logger.debug(f"Ответ Kurigram API: {result}")

    except RPCError as e:
        logger.error(f"❌ RPC ошибка при отправке подарка: {e}")
    except Exception as e:
        logger.error(f"💥 Непредвиденная ошибка при отправке коллекционного подарка: {e}", exc_info=True)


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
