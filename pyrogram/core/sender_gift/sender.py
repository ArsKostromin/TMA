import logging
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

        # Проверяем, существует ли подарок и можно ли его отправить
        try:
            gift_info = await app.get_gift(gift_id)
            logger.info(f"📦 Информация о подарке: {gift_info}")

            # Выведем ключевую инфу
            name = getattr(gift_info, "title", "Без названия")
            price = getattr(gift_info, "price", None)
            supply_left = getattr(gift_info, "supply_left", None)
            can_send = getattr(gift_info, "can_send", True)
            is_available = getattr(gift_info, "is_available", True)

            logger.info(f"🎀 Подарок: {name} | 💸 Цена: {price} | 🧮 Остаток: {supply_left} | 📤 Можно отправить: {can_send} | 🔓 Доступен: {is_available}")

            if not is_available:
                logger.warning("⚠️ Подарок больше недоступен для отправки.")
                return False
            if not can_send:
                logger.warning("⚠️ Этот подарок нельзя отправлять вручную.")
                return False
            if supply_left is not None and supply_left <= 0:
                logger.warning("⚠️ Саплай подарка закончился.")
                return False
            if price is not None and balance < price:
                logger.warning(f"⚠️ Не хватает звёзд для покупки (нужно {price}, есть {balance}).")
                return False

        except RPCError as e:
            logger.error(f"❌ Не удалось получить информацию о подарке: {e}")
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
