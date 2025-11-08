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
