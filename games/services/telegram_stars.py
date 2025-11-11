# games/services/telegram_stars.py
import logging
import requests
import json
from django.conf import settings

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
    @classmethod
    def verify_webhook_signature(cls, request) -> bool:
        """
        Проверяет секретный токен вебхука от Telegram (если задан в settings).
        """
        expected = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
        if not expected:
            return True  # если не настроен секрет — не проверяем

        actual = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not actual:
            logger.warning("⚠️ Вебхук без X-Telegram-Bot-Api-Secret-Token")
            return False

        valid = actual == expected
        if not valid:
            logger.warning(f"🚫 Неверный секрет токен вебхука: {actual}")
        return valid