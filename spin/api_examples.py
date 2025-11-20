# spin/api_examples.py
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .serializers import (
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayResponseSerializer,
    SpinPlayRequestSerializer
)


# ===============================
# 1️⃣ Spin Wheel Schema
# ===============================
def spin_wheel_schema(view_class):
    examples = [
        OpenApiExample(
            name="Пример ответа",
            value=[
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
        )
    ]

    return extend_schema(
        summary="Сектора колеса спина",
        description="Возвращает все сектора колеса спина с подарками и вероятностями",
        responses={
            200: OpenApiResponse(
                response=SpinWheelSectorSerializer(many=True),
                description="Успешный ответ",
                examples=examples
            )
        },
        tags=["spin"]
    )(view_class)


# ===============================
# 2️⃣ Spin History Schema
# ===============================
def spin_history_schema(view_class):
    example_response = {
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
                "result_sector": "3",
                "played_at": "2025-01-28T10:00:00Z"
            }
        ]
    }

    return extend_schema(
        summary="История игр в спин",
        description="Возвращает историю всех игр в спин для текущего пользователя",
        responses={
            200: OpenApiResponse(
                response=SpinGameHistorySerializer(many=True),
                description="Успешный ответ",
                examples=[OpenApiExample(name="Пример ответа", value=example_response)]
            )
        },
        tags=["spin"]
    )(view_class)


# ===============================
# 3️⃣ Spin Play Schema
# ===============================
def spin_play_schema(view_class):
    request_example = {
        "bet_stars": 100,
        "bet_ton": "5.00"
    }

    response_example = {
        "game_id": 8,
        "bet_stars": 400,
        "bet_ton": "0.000000",
        "result_sector": "2",
        "gift_won": None,
        "balances": {
            "stars": "600",
            "ton": "10.500000"
        },
        "message": "Оплатите инвойс для запуска игры"
    }

    error_example = {
        "error": "Нужна ставка в Stars или TON"
    }

    return extend_schema(
        summary="Игра в спин",
        description="Запускает игру в спин с указанными ставками в Stars и TON",
        request=SpinPlayRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SpinPlayResponseSerializer,
                description="Успешный ответ",
                examples=[OpenApiExample(name="Пример успешного ответа", value=response_example)]
            ),
            400: OpenApiResponse(
                description="Ошибка валидации",
                examples=[OpenApiExample(name="Пример ошибки", value=error_example)]
            )
        },
        tags=["Games"]
    )(view_class)
