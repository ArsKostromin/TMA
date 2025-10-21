# gifts/utils/telegram_payments.py
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def create_stars_invoice(user, gift_id: int, amount: int = 25):
    """
    Создаёт Telegram Stars-инвойс пользователю за вывод NFT.
    Требует у user: telegram_id.
    Возвращает: invoice_id, pay_url, gift_info
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
        "description": f"Вывод подарка #{gift_id}. Комиссия {amount} звёзд ⭐",
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
        
        if data.get("ok"):
            logger.info(f"✅ Инвойс успешно создан: {data}")
            return {
                "ok": True,
                "invoice_id": data["result"].get("invoice", {}).get("invoice_payload"),
                "pay_url": f"https://t.me/{bot_token.split(':')[0]}?startapp={data['result'].get('invoice', {}).get('invoice_payload')}",
                "message_id": data["result"].get("message_id"),
                "payload": data["result"].get("invoice", {}).get("invoice_payload"),
                "gift_info": {
                    "gift_id": gift_id,
                    "amount": amount
                },
                "data": data["result"]  # Для совместимости с существующим кодом
            }
        else:
            logger.error(f"💀 Telegram API вернул ошибку: {data}")
            return {"ok": False, "error": data.get("description", "Неизвестная ошибка Telegram API")}
            
    except requests.RequestException as e:
        try:
            err_data = r.json()
        except Exception:
            err_data = str(e)
        logger.error(f"💀 Не удалось создать инвойс: {e} | Ответ: {err_data}")
        return {"ok": False, "error": str(e), "details": err_data}
