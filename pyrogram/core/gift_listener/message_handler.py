import logging
import json
import requests
import config
from pyrogram.types import Message

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА ---
API_BASE_URL = getattr(config, 'API_BASE_URL', None)
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/" if API_BASE_URL else None
AUTH_TOKEN = getattr(config, 'API_TOKEN', None)


def extract_gift_data(message: Message) -> dict:
    """
    Извлекает данные о гифте из сообщения pyrogram
    """
    # В pyrogram гифт может быть в разных местах
    gift_info = None
    
    # Проверяем разные возможные места для гифта
    if hasattr(message, 'gift') and message.gift:
        gift_info = message.gift
    elif hasattr(message, 'action') and hasattr(message.action, 'gift') and message.action.gift:
        gift_info = message.action.gift
    else:
        logger.warning("⚠️ Объект 'gift' не найден в сообщении, обработка невозможна.")
        return {}
    
    # Извлекаем доступные поля
    gift_id_tg = getattr(gift_info, 'id', None)
    title = getattr(gift_info, 'title', 'Gift')
    slug = getattr(gift_info, 'slug', None)
    ton_address = slug or str(gift_id_tg) if gift_id_tg else None
    
    # Попытка извлечь rarity_level
    rarity_level = None
    if hasattr(gift_info, 'rarity_level'):
        rarity_level = getattr(gift_info.rarity_level, 'name', None)
    
    # Попытка извлечь value_amount
    value_amount = getattr(gift_info, 'value_amount', None)
    price_ton = value_amount / 100 if value_amount else None
    
    # В pyrogram атрибуты могут быть в другом формате
    attributes = getattr(gift_info, 'attributes', [])
    
    # Ищем атрибуты по типам
    model_attr = None
    pattern_attr = None
    backdrop_attr = None
    
    for attr in attributes:
        attr_type = type(attr).__name__
        if attr_type == 'StarGiftAttributeModel':
            model_attr = attr
        elif attr_type == 'StarGiftAttributePattern':
            pattern_attr = attr
        elif attr_type == 'StarGiftAttributeBackdrop':
            backdrop_attr = attr
    
    def get_details(attr_obj):
        if not attr_obj:
            return None, None, None
        
        name = getattr(attr_obj, 'name', None)
        rarity = getattr(attr_obj, 'rarity_permille', None)
        orig = getattr(attr_obj, 'original_details', None)
        orig_details = {
            "id": getattr(orig, "id", None),
            "type": getattr(orig, "type", None),
            "name": getattr(orig, "name", None),
        } if orig else None
        
        return name, rarity, orig_details

    model_name, model_rarity, model_orig = get_details(model_attr)
    pattern_name, pattern_rarity, pattern_orig = get_details(pattern_attr)
    backdrop_name, backdrop_rarity, backdrop_orig = get_details(backdrop_attr)

    gift_data = {
        "id": gift_id_tg,
        "ton_contract_address": ton_address,
        "name": title,
        "price_ton": price_ton,
        "backdrop": backdrop_name,
        "symbol": slug,
        "model_name": model_name,
        "pattern_name": pattern_name,
        "model_rarity_permille": model_rarity,
        "pattern_rarity_permille": pattern_rarity,
        "backdrop_rarity_permille": backdrop_rarity,
        "model_original_details": model_orig,
        "pattern_original_details": pattern_orig,
        "backdrop_original_details": backdrop_orig,
        "rarity_level": rarity_level,
    }

    return {k: v for k, v in gift_data.items() if v is not None}


async def send_to_django_backend(gift_data: dict):
    """
    Отправляет данные о гифте на Django бэкенд
    """
    if not API_URL:
        logger.error("❌ API_URL не установлен. Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }
    
    try:
        logger.info("=== 📤 Отправка данных в Django API ===")
        logger.info(json.dumps(gift_data, indent=4, ensure_ascii=False))
        response = requests.post(API_URL, json=gift_data, headers=headers, timeout=10)

        if 200 <= response.status_code < 300:
            logger.info(f"🎉 Успешно отправлено! Код ответа: {response.status_code}")
        else:
            logger.error(f"⚠️ Ошибка {response.status_code} при POST в Django: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при POST {API_URL}: {e}")


async def handle_star_gift(message: Message, client, **kwargs):
    """
    Обрабатывает сообщение с Star Gift
    """
    if not hasattr(message, 'action') or not message.action:
        return
        
    action_type = type(message.action).__name__
    if action_type != 'MessageActionStarGiftUnique':
        return

    sender_id = message.from_user.id if message.from_user else None
    sender_name = message.from_user.first_name if message.from_user else "Неизвестный"
    chat_title = message.chat.title or "Личные сообщения"

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в '{chat_title}'")

    gift_data = extract_gift_data(message)

    # Добавляем системные поля, нужные для передачи подарка
    gift_data.update({
        "peer_id": message.chat.id,                    # где лежит подарок
        "msg_id": message.id,                          # id конкретного сообщения
        "access_hash": getattr(message.chat, 'access_hash', None),  # нужен для InvokeWithMsgId
        "sender_id": sender_id,                        # кто прислал подарок
        "chat_name": chat_title,                       # откуда
    })

    # Добавляем URL изображения (заглушка)
    gift_data['image_url'] = "https://teststudiaorbita.ru/media/avatars/diamond.jpg"

    logger.info("--- 📦 Данные для Django ---")
    logger.info(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("-------------------------------------------")

    await send_to_django_backend(gift_data)
