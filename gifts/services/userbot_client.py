import logging
import requests

logger = logging.getLogger(__name__)

USERBOT_URL = "http://userbot:8080/test"  # имя контейнера в сети docker-compose

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
