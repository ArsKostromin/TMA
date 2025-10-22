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


# ==== Локальный тест ====
# if __name__ == "__main__":
#     import os
#     from ..telegram_client import create_client
#     import config

#     async def main():
#         app = create_client(config)
#         await app.start()

#         peer_id = 1207534564  # id получателя
#         gift_id = 5852757491946882427  # id гифта SnakeBox-29826

#         success = await send_gift_to_user(app, peer_id, gift_id)

#         if success:
#             logger.info("🎉 Тестовая отправка прошла успешно!")
#         else:
#             logger.error("💀 Тестовая отправка не удалась!")

#         await app.stop()

#     asyncio.run(main())
