import logging
from decimal import Decimal
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from user.telegram_stars import TelegramStarsService
from spin.models import SpinGame
from .spin_service import SpinService
import time


logger = logging.getLogger(__name__)

class SpinBetService:

    @staticmethod
    async def validate_user(user):
        if not user.telegram_id:
            raise ValidationError("У аккаунта не указан Telegram ID (telegram_id)")

    @staticmethod
    async def create_invoice_for_stars(user, bet_stars: int, channel_name: str) -> dict:
        """
        Создаёт инвойс для оплаты звёздами. Игра ещё не создаётся.
        """
        # Проверка пользователя
        await SpinBetService.validate_user(user)

        # Генерируем короткий уникальный ID заказа для payload (Telegram требует строку <= 32 байт)
        payload = channel_name  # строго строка, короткая и уникальная

        # Заголовки инвойса
        title = "Ставка в рулетку"
        description = f"Оплата участия в спин-игре. Ставка: {bet_stars}⭐"

        logger.warning("вызвался create_invoice_for_stars!Й!!")

        # Создаём инвойс через TelegramStarsService (sync -> async)
        invoice_result = await sync_to_async(TelegramStarsService.create_invoice)(
            amount_stars=bet_stars,
            title=title,
            description=description,
            payload=payload 
        )

        if not invoice_result.get("ok"):
            raise ValidationError(f"Не удалось создать инвойс: {invoice_result.get('error')}")

        return {
            "payment_required": True,
            "payment_link": invoice_result.get("invoice_link"),
            "bet_stars": bet_stars,
            "message": "Оплатите инвойс для запуска игры",
        }

    @staticmethod
    async def create_game_after_payment(user, bet_stars: int, bet_ton: Decimal) -> dict:
        """
        Создаёт игру **после успешной оплаты**.
        """
        # синхронно создаём игру с транзакцией
        @sync_to_async
        def create_game():
            return SpinGame.objects.create(
                player=user,
                bet_stars=bet_stars,
                bet_ton=bet_ton,
                result_sector=None
            )

        game = await create_game()
        return {
            "game_id": game.id,
            "bet_stars": bet_stars,
            "bet_ton": str(bet_ton),
            "message": "Игра создана после успешной оплаты"
        }

    @staticmethod
    async def create_bet_with_ton(user, bet_ton: Decimal) -> dict:
        """
        Ставка в TON остаётся как раньше — списываем и сразу запускаем игру.
        """
        if user.balance_ton < bet_ton:
            raise ValidationError("Недостаточно TON на балансе")

        await sync_to_async(user.subtract_ton)(bet_ton)

        @sync_to_async
        def play_game():
            return SpinService.play(user, bet_stars=0, bet_ton=bet_ton)

        game, result = await play_game()

        return {
            "game_id": game.id,
            "payment_required": False,
            "payment_link": None,
            "bet_stars": 0,
            "bet_ton": str(bet_ton),
            "result_sector": result.index,
            "gift_won": result.gift,
            "balances": {
                "stars": user.balance_stars,
                "ton": str(user.balance_ton),
            }
        }
