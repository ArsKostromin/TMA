# games/services/telegram_stars.py
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramStarsService:
    """
    Сервис для работы с Telegram Stars инвойсами.
    Создаёт инвойсы для оплаты звёздами через Bot API.
    """
    
    @classmethod
    def get_bot_token(cls):
        """Получает токен бота из настроек"""
        return getattr(settings, 'BOT_TOKEN', None)
    
    @classmethod
    def create_invoice(cls, user_id: int, order_id: int, amount_stars: int, title: str = None, description: str = None) -> dict:
        """
        Создаёт Telegram Stars инвойс для пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            order_id: ID заказа (game_id для спин игры)
            amount_stars: Количество звёзд для оплаты
            title: Заголовок инвойса (опционально)
            description: Описание инвойса (опционально)
        
        Returns:
            dict с результатом создания инвойса:
            {
                "ok": True/False,
                "invoice_link": "ссылка на оплату" (если успешно),
                "error": "текст ошибки" (если ошибка)
            }
        """
        bot_token = cls.get_bot_token()
        if not bot_token:
            logger.error("❌ BOT_TOKEN не найден в settings")
            return {
                "ok": False,
                "error": "BOT_TOKEN не настроен"
            }
        
        url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"
        
        payload = {
            "chat_id": user_id,
            "title": title or "Ставка в рулетку",
            "description": description or "Оплата участия звёздами",
            "payload": f"spin_game_{order_id}",  # формат: spin_game_{game_id}
            "currency": "XTR",  # XTR = Telegram Stars
            "prices": [{"label": "Bet", "amount": amount_stars}],
            "provider_token": "",  # для Stars — оставляем пустым
        }
        
        logger.info(f"🧾 Создание инвойса: user_id={user_id}, order_id={order_id}, amount={amount_stars}")
        
        try:
            resp = requests.post(url, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("ok"):
                # Извлекаем invoice_link из результата
                result = data.get("result", {})
                invoice_link = result.get("invoice", {}).get("invoice_link") or result.get("invoice_link")
                
                if invoice_link:
                    logger.info(f"✅ Инвойс успешно создан: invoice_link={invoice_link}")
                    return {
                        "ok": True,
                        "invoice_link": invoice_link,
                        "message_id": result.get("message_id"),
                        "invoice_payload": f"spin_game_{order_id}"
                    }
                else:
                    logger.warning(f"⚠️ Инвойс создан, но invoice_link не найден: {data}")
                    return {
                        "ok": True,
                        "invoice_link": None,
                        "data": data
                    }
            else:
                error_msg = data.get("description", "Неизвестная ошибка Telegram API")
                logger.error(f"❌ Telegram API вернул ошибку: {error_msg}")
                return {
                    "ok": False,
                    "error": error_msg
                }
                
        except requests.RequestException as e:
            logger.exception(f"❌ Ошибка при создании инвойса: {e}")
            try:
                err_data = resp.json() if 'resp' in locals() else str(e)
            except Exception:
                err_data = str(e)
            return {
                "ok": False,
                "error": str(e),
                "details": err_data
            }

