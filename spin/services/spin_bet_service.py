import logging
from decimal import Decimal
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from user.services.telegram_stars import TelegramStarsService
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

    @staticmethod
    async def create_bet_with_stars(user, bet_stars: int) -> dict:
        """
        Ставка в stars остаётся как раньше — списываем и сразу запускаем игру.
        """
        if user.balance_stars < bet_stars:
            raise ValidationError("Недостаточно stars на балансе")

        await sync_to_async(user.subtract_stars)(bet_stars)

        @sync_to_async
        def play_game():
            return SpinService.play(user, bet_stars=bet_stars, bet_ton=0)

        game, result = await play_game()

        return {
            "game_id": game.id,
            "payment_required": False,
            "bet_stars": str(bet_stars),
            "bet_ton": 0,
            "result_sector": result.index,
            "gift_won": result.gift,
            "balances": {
                "stars": user.balance_stars,
                "ton": str(user.balance_ton),
            }
        }
