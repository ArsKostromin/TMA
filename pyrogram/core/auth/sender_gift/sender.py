import logging
import asyncio
from pyrogram import Client
from pyrogram.errors import RPCError

logger = logging.getLogger("pyrogram-main.sender")


async def send_gift_to_user(app: Client, peer_id: int, gift_id: int):
    """
    Отправляет подарок (NFT) пользователю через Pyrogram метод send_gift.
    
    :param app: Инициализированный клиент Pyrogram
    :param peer_id: Telegram ID получателя
    :param gift_id: ID подарка (NFT)
    """
    try:
        logger.info(f"🎁 Отправляем подарок ID={gift_id} пользователю ID={peer_id} ...")
        
        # Отправляем подарок через API Pyrogram
        result = await app.send_gift(
            peer_id=peer_id,       # ID юзера
            gift_id=gift_id,       # ID подарка (NFT)
            slug=None,             # Можно передать slug, если требуется
            currency="TON",        # Валюта оплаты
            comment="От души 💜🐍", # Комментарий при дарении
        )

        logger.info(f"✅ Подарок успешно отправлен! Ответ API: {result}")
        return result

    except RPCError as e:
        logger.error(f"❌ Ошибка RPC при отправке подарка: {e}")
    except Exception as e:
        logger.error(f"💥 Непредвиденная ошибка при отправке подарка: {e}")
    return None


# Если нужно локально протестировать вручную
if __name__ == "__main__":
    from ..telegram_client import create_client
    import config

    async def main():
        app = create_client(config)
        await app.start()

        # данные пользователя и подарка
        peer_id = 1207534564   # получатель jhgvcbcg
        gift_id = 5852757491946882427  # ID гифта SnakeBox-29826

        await send_gift_to_user(app, peer_id, gift_id)
        await app.stop()

    asyncio.run(main())