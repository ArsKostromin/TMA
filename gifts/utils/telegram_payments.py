import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def create_stars_invoice(user, gift_id: int, amount: int = 25):
    """
    Создаёт Telegram Stars-инвойс (оплата XTR) пользователю за вывод NFT.
    Требует, чтобы у user был telegram_id и в settings.bot_token был токен бота.
    """
    bot_token = getattr(settings, "STAR_TOKEN", None)
    if not bot_token:
        logger.error("❌ В settings.py отсутствует bot_token", settings.star_token)

        return {"ok": False, "error": "bot_token отсутствует"}

    if not hasattr(user, "telegram_id") or not user.telegram_id:
        logger.error(f"🚫 У пользователя {user.id} нет telegram_id")
        return {"ok": False, "error": "У пользователя нет telegram_id"}

    tg_url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"
    payload = {
        "chat_id": user.telegram_id,
        "title": "Вывод NFT подарка",
        "description": f"Оплата комиссии  {amount}⭐ за вывод подарка",
        "payload": f"withdraw_{gift_id}_{user.id}",
        "provider_token": "", 
        "currency": "XTR",
        "prices": [{"label": "Комиссия за вывод", "amount": amount}],
        "start_parameter": f"withdraw_{gift_id}",
    }

    try:
        r = requests.post(tg_url, json=payload)
        r.raise_for_status()
        result = r.json()

        if not result.get("ok"):
            logger.error(f"💀 Ошибка Telegram API при создании инвойса: {result}")
            return {"ok": False, "error": result}

        logger.info(f"💫 Инвойс на {amount}⭐ успешно отправлен пользователю {user.username}")
        return {
            "ok": True,
            "data": result.get("result", {}),
            "payload": payload,
        }

    except requests.RequestException as e:
        logger.exception("💀 Ошибка при запросе к Telegram API")
        return {"ok": False, "error": str(e)}
