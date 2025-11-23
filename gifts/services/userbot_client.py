import logging
import os
import requests

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("USERBOT_BASE_URL", "http://userbot:8080")
USERBOT_URL = f"{BASE_URL}/test"  # имя контейнера в сети docker-compose

def send_test_request_to_userbot(payload: dict) -> bool:
    """
    Пробный запрос в userbot, чтобы убедиться, что связь работает.
    """
    logger.info(f"🚀 Отправляю запрос в userbot: {USERBOT_URL} с данными: {payload}")

    try:
        resp = requests.post(USERBOT_URL, json=payload, timeout=10)
        logger.info(f"✅ Ответ от userbot: {resp.status_code} - {resp.text}")
        return resp.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при отправке запроса в userbot: {e}")
        return False


def create_star_invoice_via_userbot(chat_id: int, gift_id: int, amount: int = 25, title: str | None = None, description: str | None = None) -> dict:
    """
    Создать инвойс на оплату звёздами через сервис userbot.
    Возвращает dict c полями ok, chat_id, message_id, payload, amount, currency.
    """
    url = f"{BASE_URL}/create_star_invoice"
    payload = {
        "chat_id": chat_id,
        "gift_id": gift_id,
        "amount": amount,
        "title": title,
        "description": description,
    }
    logger.info(f"🧾 Запрос на создание звёздного инвойса в userbot: {url} | {payload}")
    try:
        r = requests.post(url, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        logger.info(f"✅ Ответ от userbot (invoice): {data}")
        return data
    except requests.exceptions.RequestException as e:
        try:
            err = r.json()
        except Exception:
            err = str(e)
        logger.error(f"❌ Ошибка при создании инвойса через userbot: {e} | {err}")
        return {"ok": False, "error": str(e), "details": err}


def send_gift_via_userbot(gift_id: int, recipient_telegram_id: int, ton_contract_address: str = None, msg_id=None) -> dict:
    """
    Отправить подарок пользователю через сервис userbot.
    Выполняет реальную отправку подарка через Telegram.
    
    Args:
        gift_id: ID подарка в Django БД
        recipient_telegram_id: Telegram ID получателя подарка
        ton_contract_address: Уникальный slug подарка (используется для поиска в инвентаре)
        msg_id: ID сообщения с подарком (опционально, если не указан - будет найден по ton_contract_address)
    
    Returns:
        dict с результатом отправки: {"ok": bool, "message": str, "data": dict}
    """
    url = f"{BASE_URL}/send_gift"
    payload = {
        "gift_id": gift_id,
        "recipient_telegram_id": recipient_telegram_id,
    }
    if ton_contract_address:
        # Убеждаемся, что передаем строку
        payload["ton_contract_address"] = str(ton_contract_address) if ton_contract_address else None
        logger.debug(f"📝 Добавлен ton_contract_address в payload: {payload['ton_contract_address']} (тип: {type(payload['ton_contract_address']).__name__})")
    if msg_id:
        payload["msg_id"] = msg_id
    
    logger.info(f"🎁 Запрос на отправку подарка через userbot: {url}")
    logger.debug(f"📦 Payload: {payload}")
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        logger.info(f"✅ Ответ от userbot (send_gift): {data}")
        return data
    except requests.exceptions.HTTPError as e:
        # Ошибка HTTP (4xx, 5xx)
        try:
            err = e.response.json() if e.response else {}
        except Exception:
            err = {"error": str(e), "status_code": e.response.status_code if e.response else None}
        logger.error(f"❌ HTTP ошибка при отправке подарка через userbot: {e} | {err}")
        return {"ok": False, "error": str(e), "details": err}
    except requests.exceptions.RequestException as e:
        # Сетевая ошибка или другая ошибка запроса
        logger.error(f"❌ Ошибка при отправке подарка через userbot: {e}")
        return {"ok": False, "error": str(e), "details": {"error": str(e)}}