import logging
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class UserbotTransferResult:
    ok: bool
    status: int
    data: dict | None = None
    error: str | None = None


class UserbotClient:
    """
    Клиент для обращения к userbot-сервису, который реально совершает передачу подарка в Telegram.
    Ожидается HTTP API от userbot:
      POST {USERBOT_API_URL}/api/transfer-gift
      Body JSON: {
          "from_telegram_id": int,       # телеграм id userbot аккаунта-отправителя (опц.)
          "to_telegram_id": int,         # телеграм id получателя (наш пользователь)
          "gift_id": str,                # идентификатор подарка (ton_contract_address)
          "fee_stars": int               # комиссия в звёздах (25)
      }
      Headers: Authorization: Bearer <USERBOT_API_TOKEN>
    Ответ 200: { "ok": true, "tx_id": "...", ... }
    Ответ !=200: { "ok": false, "error": "..." }
    """

    @staticmethod
    def transfer_gift(to_telegram_id: int, gift_contract_address: str, fee_stars: int = 25,
                       from_telegram_id: Optional[int] = None) -> UserbotTransferResult:
        base_url: Optional[str] = getattr(settings, "USERBOT_API_URL", None)
        api_token: Optional[str] = getattr(settings, "USERBOT_API_TOKEN", None)
        if not base_url or not api_token:
            msg = "USERBOT_API_URL/USERBOT_API_TOKEN не настроены"
            logger.error(f"[UserbotClient] {msg}")
            return UserbotTransferResult(ok=False, status=500, error=msg)

        url = f"{base_url.rstrip('/')}/api/transfer-gift"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "to_telegram_id": to_telegram_id,
            "gift_id": gift_contract_address,
            "fee_stars": fee_stars
        }
        if from_telegram_id:
            payload["from_telegram_id"] = from_telegram_id

        try:
            logger.info(f"[UserbotClient] POST {url} -> {payload}")
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            content: dict | None = None
            try:
                content = resp.json()
            except Exception:
                content = {"text": resp.text[:500]}

            ok = resp.status_code == 200 and bool(content and content.get("ok", False))
            if ok:
                logger.info(f"[UserbotClient] Успех передачи подарка: {content}")
                return UserbotTransferResult(ok=True, status=resp.status_code, data=content)
            else:
                err = (content or {}).get("error") or f"HTTP {resp.status_code}"
                logger.warning(f"[UserbotClient] Ошибка передачи подарка: {content}")
                return UserbotTransferResult(ok=False, status=resp.status_code, data=content, error=err)
        except requests.RequestException as e:
            logger.exception(f"[UserbotClient] Сетевая ошибка: {e}")
            return UserbotTransferResult(ok=False, status=500, error=str(e))
