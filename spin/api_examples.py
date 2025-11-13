# Примеры ответов для API эндпоинтов игр
# Используется в @extend_schema для качественной документации



# SpinPlayView
SPIN_PLAY_REQUEST_EXAMPLE = {
    "bet_stars": 100,
    "bet_ton": "5.00"
}

SPIN_PLAY_RESPONSE_EXAMPLE = {
    "game_id": 8,
    "bet_stars": 400,
    "bet_ton": "0",
    "payment_required": True,
    "payment_link": "https://t.me/$1QwvxHKimEhjEAAAwGyRljZRj1Y",
    "message": "Оплатите инвойс для запуска игры"
}

# SpinWheelView
SPIN_WHEEL_EXAMPLE = [
    {
        "index": 0,
        "probability": "15.0",
        "gift": {
            "id": 123,
            "name": "Common Coin",
            "description": "Обычная монета",
            "image_url": "https://example.com/coin.png",
            "price_ton": "1.00",
            "rarity": "common"
        }
    },
    {
        "index": 1,
        "probability": "5.0",
        "gift": {
            "id": 456,
            "name": "Epic Dragon",
            "description": "Эпический дракон",
            "image_url": "https://example.com/dragon.png",
            "price_ton": "25.00",
            "rarity": "epic"
        }
    }
]

# SpinGameHistoryView
SPIN_GAME_HISTORY_EXAMPLE = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": 15,
            "bet_stars": 100,
            "bet_ton": "5.00",
            "win_amount": "25.00",
            "gift_won": {
                "id": 456,
                "name": "Epic Dragon",
                "description": "Эпический дракон",
                "image_url": "https://example.com/dragon.png",
                "price_ton": "25.00",
                "rarity": "epic"
            },
            "result_sector": 3,
            "played_at": "2025-01-28T10:00:00Z"
        }
    ]
}