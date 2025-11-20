# games/utils/spin_response.py
from typing import Optional
from gifts.models import Gift


def format_gift_won(gift: Optional[Gift]) -> Optional[dict]:
    if not gift:
        return None

    return {
        "id": gift.id,
        "user_username": gift.user.username if gift.user else None,
        "ton_contract_address": gift.ton_contract_address,
        "name": gift.name,
        "image_url": gift.image_url,
        "price_ton": str(gift.price_ton),
        "backdrop": gift.backdrop,
        "symbol": gift.symbol,
        "model_name": gift.model_name,
        "pattern_name": gift.pattern_name,
        "model_rarity_permille": gift.model_rarity_permille,
        "pattern_rarity_permille": gift.pattern_rarity_permille,
        "backdrop_rarity_permille": gift.backdrop_rarity_permille,
        "model_original_details": gift.model_original_details,
        "pattern_original_details": gift.pattern_original_details,
        "backdrop_original_details": gift.backdrop_original_details,
        "rarity_level": gift.rarity_level,
        "backdrop_name": getattr(gift, "backdrop_name", None),
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
