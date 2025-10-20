# gifts/utils/telegram_payments.py
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def create_stars_invoice(user, gift_id: int, amount: int = 25):
    """
    Создаёт Telegram Stars-инвойс пользователю за вывод NFT.
    Требует у user: telegram_id.
    """
    bot_token = getattr(settings, "STAR_TOKEN", None)
    if not bot_token:
        logger.error("❌ В settings.py отсутствует star_token (None)")
        return {"ok": False, "error": "star_token отсутствует"}

    chat_id = getattr(user, "telegram_id", None)
    if not chat_id:
        logger.error(f"🚫 У пользователя {user.id} нет telegram_id")
        return {"ok": False, "error": "telegram_id отсутствует"}

    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"

    payload = {
        "chat_id": chat_id,
        "title": "Оплата вывода NFT",
        "description": f"Вывод подарка #{gift_id}. Комиссия 25 звёзд ⭐",
        "payload": f"withdraw_gift_{gift_id}",
        "provider_token": "",  # для Stars — оставить пустым!
        "currency": "XTR",
        "prices": [{"label": "Комиссия", "amount": amount}],
        "max_tip_amount": 0,
        "suggested_tip_amounts": [],
    }

    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        logger.info(f"✅ Инвойс успешно создан: {data}")
        return data
    except requests.RequestException as e:
        try:
            err_data = r.json()
        except Exception:
            err_data = str(e)
        logger.error(f"💀 Не удалось создать инвойс: {e} | Ответ: {err_data}")
        return {"ok": False, "error": str(e), "details": err_data}
