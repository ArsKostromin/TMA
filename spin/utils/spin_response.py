# games/utils/spin_response.py
from typing import Optional
from gifts.models import Gift


def format_gift_won(gift: Optional[Gift]) -> Optional[dict]:
    if not gift:
        return None

    return {
        "id": gift.id,
        "name": gift.name,
        "image_url": gift.image_url,
        "price_ton": str(gift.price_ton),
        "rarity": getattr(gift, "rarity_level", None),
    }


def format_spin_response(data: dict) -> dict:
    """
    Форматирует ответ для SpinPlayView без payment_required и payment_link.
    """
    return {
        "game_id": data["game_id"],
        "bet_stars": data["bet_stars"],
        "bet_ton": data["bet_ton"],
        "result_sector": data.get("result_sector"),
        "gift_won": format_gift_won(data.get("gift_won")),
        "balances": data.get("balances", {}),
    }
