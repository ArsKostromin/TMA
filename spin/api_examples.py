# api_docs/spin_docs.py

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample
)
from ..serializers import (
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayRequestSerializer,
    SpinPlayResponseSerializer,
)
from ..api_examples import (
    SPIN_WHEEL_EXAMPLE,
    SPIN_GAME_HISTORY_EXAMPLE,
    SPIN_PLAY_RESPONSE_EXAMPLE
)


# ---- SpinWheelView ----
spin_wheel_schema = extend_schema(
    summary="Сектора колеса спина",
    description="Возвращает все сектора колеса спина с подарками и вероятностями",
    responses={
        200: OpenApiResponse(
            response=SpinWheelSectorSerializer(many=True),
            description="Успешный ответ",
            examples=[
                OpenApiExample(
                    name="Пример ответа",
                    value=SPIN_WHEEL_EXAMPLE
                )
            ],
        ),
    },
    tags=["spin"],
)


# ---- SpinGameHistoryView ----
spin_history_schema = extend_schema(
    summary="История игр в спин",
    description="Возвращает историю всех игр в спин для текущего пользователя",
    responses={
        200: OpenApiResponse(
            response=SpinGameHistorySerializer,
            description="Успешный ответ",
            examples=[
                OpenApiExample(
                    name="Пример ответа",
                    value=SPIN_GAME_HISTORY_EXAMPLE
                )
            ],
        ),
    },
    tags=["spin"],
)


# ---- SpinPlayView ----
spin_play_schema = extend_schema(
    summary="Игра в спин",
    description="Запускает игру в спин с указанными ставками в Stars и TON",
    request=SpinPlayRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=SpinPlayResponseSerializer,
            description="Успешный ответ",
            examples=[
                OpenApiExample(
                    name="Пример ответа",
                    value=SPIN_PLAY_RESPONSE_EXAMPLE
                )
            ],
        ),
        400: OpenApiResponse(description="Ошибка валидации"),
    },
    tags=["Games"],
)
