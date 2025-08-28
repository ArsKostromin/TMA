# Примеры ответов для API эндпоинтов игр
# Используется в @extend_schema для качественной документации

# GameHistoryView
GAME_HISTORY_EXAMPLE = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": 4,
            "mode": "pvp",
            "status": "finished",
            "pot_amount_ton": "15.00",
            "started_at": "2025-01-28T10:00:00Z",
            "ended_at": "2025-01-28T10:00:40Z",
            "winner_id": 3,
            "is_winner": True,
            "player_data": {
                "bet_ton": "15.00",
                "chance_percent": "100.0",
                "gifts": [
                    {
                        "id": 123,
                        "name": "Rare Cat NFT",
                        "image_url": "https://example.com/cat.png"
                    }
                ]
            }
        }
    ]
}

# TopPlayersAPIView
TOP_PLAYER_EXAMPLE = {
    "id": 3,
    "username": "GameGaKuSeI",
    "avatar_url": "https://example.com/avatar.png",
    "wins_count": 5,
    "total_wins_ton": "150.00"
}

# PvPGameHistoryAPIView
PVP_GAME_HISTORY_EXAMPLE = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": 4,
            "hash": "abc123def456...",
            "started_at": "2025-01-28T10:00:00Z",
            "detail_url": "/games/pvp-game/4/",
            "winner": {
                "id": 3,
                "username": "GameGaKuSeI",
                "avatar_url": "https://example.com/avatar.png"
            },
            "winner_gift_icons": [
                "https://example.com/cat.png",
                "https://example.com/dog.png"
            ],
            "win_amount_ton": "12.75",
            "winner_chance_percent": "50.0"
        }
    ]
}

# PvpGameDetailView
PVP_GAME_DETAIL_EXAMPLE = {
    "id": 4,
    "hash": "abc123def456...",
    "started_at": "2025-01-28T10:00:00Z",
    "ended_at": "2025-01-28T10:00:40Z",
    "winner": {
        "id": 3,
        "username": "GameGaKuSeI",
        "avatar_url": "https://example.com/avatar.png"
    },
    "winner_gifts": [
        {
            "id": 123,
            "name": "Rare Cat NFT",
            "image_url": "https://example.com/cat.png",
            "price_ton": "10.00"
        }
    ],
    "win_amount_ton": "12.75",
    "winner_chance_percent": "50.0"
}

# SpinPlayView
SPIN_PLAY_REQUEST_EXAMPLE = {
    "bet_stars": 100,
    "bet_ton": "5.00"
}

SPIN_PLAY_RESPONSE_EXAMPLE = {
    "game_id": 15,
    "bet_stars": 100,
    "bet_ton": "5.00",
    "result_sector": 3,
    "gift_won": {
        "id": 456,
        "name": "Epic Dragon",
        "image_url": "https://example.com/dragon.png",
        "price_ton": "25.00",
        "rarity": "epic"
    },
    "balances": {
        "stars": 900,
        "ton": "95.00"
    }
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

# LastPvpWinnerView
LAST_WINNER_EXAMPLE = {
    "id": 3,
    "username": "GameGaKuSeI",
    "avatar_url": "https://example.com/avatar.png",
    "total_bet_ton": "15.00",
    "chance_percent": "50.0",
    "win_amount": "12.75",
    "game_id": 4
}
