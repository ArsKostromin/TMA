import logging
from pyrogram import filters
from pyrogram.types import Message
from .message_handler import handle_star_gift

logger = logging.getLogger(__name__)

def register_gift_listener(app):
    """
    Подписка на ВСЕ НОВЫЕ сообщения (real-time).
    """
    @app.on_message(filters.all)
    async def handle_new_gift(client, message: Message):
        # Проверяем, есть ли действие в сообщении
        if not hasattr(message, 'action') or not message.action:
            return
            
        # Проверяем тип действия - это должен быть Star Gift
        action_type = type(message.action).__name__
        if action_type != 'MessageActionStarGiftUnique':
            return
            
        chat_title = message.chat.title or "Личные сообщения"
        logger.info(f"🎁 (Real-Time) Новый NFT: {action_type} в чате '{chat_title}'")
        
        try:
            # Обрабатываем, отправляем на бэкенд, логируем
            await handle_star_gift(message, client)
            
            # Помечаем сообщение как прочитанное
            await client.read_chat_history(message.chat.id, message.id)
            
        except Exception as e:
            logger.error(f"⚠️ Ошибка при обработке нового NFT: {e}")


async def process_chat_history(client):
    """
    Проходит по истории ВСЕХ диалогов, обрабатывая ТОЛЬКО НЕПРОЧИТАННЫЕ сообщения
    с подарками, и помечает их как прочитанные после обработки.
    """
    logger.info("⏳ Начинаю обработку истории: ищем НЕПРОЧИТАННЫЕ NFT-подарки...")
    total_processed_gifts = 0
    total_scanned_chats = 0
    
    # Итерируем по всем диалогам
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        chat_title = chat.title or "Личные сообщения"
        processed_count = 0
        total_scanned_chats += 1
        
        # Проверяем наличие непрочитанных сообщений в диалоге
        if dialog.unread_messages_count == 0:
            continue
        
        logger.info(f"🔎 Сканирование НЕПРОЧИТАННОЙ истории чата: '{chat_title}' (Непрочитанных: {dialog.unread_count})")
        
        processed_ids = []
        
        # Итерируем сообщения. Лимит 2000 для охвата недавних сообщений.
        async for message in client.get_chat_history(chat.id, limit=2000):
            # Проверяем наличие действия и гифта
            if not hasattr(message, 'action') or not message.action:
                continue
                
            action_type = type(message.action).__name__
            if action_type != 'MessageActionStarGiftUnique':
                continue
                
            processed_count += 1
            total_processed_gifts += 1
            
            logger.warning(f"📜 (Unread History) Найден NFT в MSG_ID: {message.id} в чате '{chat_title}'")
            logger.warning(f"📜 (Unread History) '{message}'")
            
            try:
                await handle_star_gift(message, client)
                processed_ids.append(message.id)
            except Exception as e:
                logger.error(f"⚠️ Ошибка при обработке NFT из истории (MSG_ID: {message.id}, Чат: {chat_title}): {e}")
        
        # Помечаем все обработанные подарки (в этом чате) как прочитанные
        if processed_ids:
            try:
                # Отмечает сообщения как прочитанные
                await client.read_chat_history(chat.id, max_id=max(processed_ids))
                logger.info(f"☑️ Помечено как прочитанное {len(processed_ids)} NFT в чате '{chat_title}'.")
            except Exception as e:
                logger.error(f"❌ Не удалось пометить сообщения {processed_ids} как прочитанные: {e}")
        
        logger.info(f"✅ Обработка непрочитанных сообщений в чате '{chat_title}' завершена. Найдено NFT: {processed_count}.")
    
    logger.info(f"🎉 Обработка истории завершена. Всего просканировано чатов: {total_scanned_chats}. Всего найдено NFT: {total_processed_gifts}.")
