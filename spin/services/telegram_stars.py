# spin/services/telegram_stars.py
import logging
import requests
import json
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


logger = logging.getLogger(__name__)


class TelegramStarsService:
    """
    Сервис для работы с Telegram Stars инвойсами.
    Создаёт инвойсы для оплаты звёздами через Bot API (метод createInvoiceLink).
    """

    TELEGRAM_API_URL = "https://api.telegram.org"

    @classmethod
    def get_bot_token(cls) -> str:
        """Получает токен бота из settings."""
        token = getattr(settings, "BOT_TOKEN", None)
        if not token:
            logger.error("❌ BOT_TOKEN не найден в settings.py")
        return token

    # ========================
    # 🔹 СОЗДАНИЕ ИНВОЙСА
    # ========================
    @classmethod
    def create_invoice(
        cls,
        order_id: int,
        amount_stars: int,
        title: str = None,
        description: str = None,
    ) -> dict:
        """
        Создаёт ссылку на Telegram Stars-инвойс для Mini App.
        Возвращает только ссылку (не отправляет сообщение пользователю).
        """
        bot_token = cls.get_bot_token()
        if not bot_token:
            return {"ok": False, "error": "BOT_TOKEN не настроен"}

        url = f"{cls.TELEGRAM_API_URL}/bot{bot_token}/createInvoiceLink"

        # создаём payload для webhook'а
        payload_data = {
            "order_id": order_id,
            "type": "spin_game",
        }

        payload = {
            "title": title or "Ставка в рулетку",
            "description": description or f"Оплата участия в спин-игре #{order_id}",
            "payload": json.dumps(payload_data, ensure_ascii=False),
            "currency": "XTR",  # Telegram Stars = XTR
            "prices": [{"label": "Bet", "amount": amount_stars}],
            "provider_token": "",  # обязательно пустое поле для Stars
        }

        logger.info(f"🧾 Создание Stars-инвойса: game_id={order_id}, amount={amount_stars}")

        try:
            response = requests.post(url, json=payload, timeout=20)
            data = response.json()

            if not data.get("ok"):
                logger.error(f"❌ Ошибка Telegram API: {data}")
                return {
                    "ok": False,
                    "error": data.get("description", "Ошибка Telegram API"),
                    "raw": data,
                }

            invoice_link = data.get("result")
            logger.info(f"✅ Ссылка на инвойс: {invoice_link}")

            return {
                "ok": True,
                "invoice_link": invoice_link,
                "invoice_payload": payload_data,
            }

        except requests.RequestException as e:
            logger.exception("❌ Ошибка при запросе к Telegram API")
            return {"ok": False, "error": str(e)}

    # ========================
    # 🔹 ПРОВЕРКА ВЕБХУКА
    # ========================
class SocketNotifyService:
    """
    Сервис для уведомления WebSocket-клиентов.
    """

    @staticmethod
    def send_to_socket(socket_id: str, event_type: str, data: dict):
        """
        Отправляет сообщение в сокет-группу.
        """
        if not socket_id:
            logger.warning("Попытка отправить уведомление без socket_id")
            return False

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"socket_{socket_id}",
            {
                "type": event_type,
                "data": data,
            },
        )

        logger.info(f"Сообщение отправлено в socket_{socket_id}: {event_type}")
        return True