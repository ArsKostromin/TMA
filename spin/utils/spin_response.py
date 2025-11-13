# games/utils/spin_response.py
from typing import Optional
from gifts.models import Gift


def format_gift_won(gift: Optional[Gift]) -> Optional[dict]:
    """
    Форматирует информацию о выигранном подарке для ответа API.
    
    Args:
        gift: Объект подарка или None
    
    Returns:
        dict с данными подарка или None
    """
    if not gift:
        return None
    
    return {
        "id": gift.id,
        "name": gift.name,
        "image_url": gift.image_url,
        "price_ton": str(gift.price_ton),
        "rarity": getattr(gift, 'rarity_level', None),
    }


def format_spin_response(data: dict) -> dict:
    """
    Форматирует ответ для SpinPlayView.
    
    Args:
        data: Данные от SpinBetService
    
    Returns:
        Отформатированный ответ для API
    """
    response = {
        "game_id": data["game_id"],
        "bet_stars": data["bet_stars"],
        "bet_ton": data["bet_ton"],
        "payment_required": data.get("payment_required", False),
    }
    
    # Если требуется оплата
    if data.get("payment_required"):
        response.update({
            "payment_link": data.get("payment_link"),
            "message": data.get("message", "Оплатите инвойс для запуска игры")
        })
    else:
        # Игра уже завершена
        response.update({
            "payment_link": None,
            "result_sector": data.get("result_sector"),
            "gift_won": format_gift_won(data.get("gift_won")),
            "balances": data.get("balances", {})
        })
    
    return response

