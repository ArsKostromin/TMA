import logging
from decimal import Decimal
from django.core.exceptions import ValidationError
from spin.models import SpinGame
from .spin_service import SpinService

logger = logging.getLogger(__name__)

class SpinBetService:

    @staticmethod
    def validate_user(user):
        if not user.telegram_id:
            raise ValidationError("У аккаунта не указан Telegram ID (telegram_id)")

    @staticmethod
    def create_bet_with_ton(user, bet_ton: Decimal) -> dict:
        """
        Ставка в TON: списываем баланс и сразу играем.
        Полностью синхронно.
        """
        if user.balance_ton < bet_ton:
            raise ValidationError("Недостаточно TON на балансе")

        # списываем
        user.subtract_ton(bet_ton)

        # играем
        game, result = SpinService.play(user, bet_stars=0, bet_ton=bet_ton)

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
    def create_bet_with_stars(user, bet_stars: int) -> dict:
        """
        Ставка в Stars: списываем и сразу играем.
        Полностью синхронно.
        """
        if user.balance_stars < bet_stars:
            raise ValidationError("Недостаточно Stars на балансе")

        # списываем
        user.subtract_stars(bet_stars)

        # играем
        game, result = SpinService.play(user, bet_stars=bet_stars, bet_ton=0)

        return {
            "game_id": game.id,
            "payment_required": False,
            "payment_link": None,
            "bet_stars": bet_stars,
            "bet_ton": "0",
            "result_sector": result.index,
            "gift_won": result.gift,
            "balances": {
                "stars": user.balance_stars,
                "ton": str(user.balance_ton),
            }
        }
