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
    def create_bet_with_ton(user, bet_ton: Decimal) -> dict:
        """
        Ставка в TON — списываем и сразу запускаем игру.
        """
        if user.balance_ton < bet_ton:
            raise ValidationError("Недостаточно TON на балансе")

        # Синхронное списание TON
        user.subtract_ton(bet_ton)

        # Синхронный запуск игры
        game, result = SpinService.play(user, bet_stars=0, bet_ton=bet_ton)

        return {
            "game_id": game.id,
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
        Ставка в Stars — списываем и запускаем игру.
        """
        if user.balance_stars < bet_stars:
            raise ValidationError("Недостаточно stars на балансе")

        # Синхронное списание Stars
        user.subtract_stars(bet_stars)

        # Синхронный запуск игры
        game, result = SpinService.play(user, bet_stars=bet_stars, bet_ton=0)

        return {
            "game_id": game.id,
            "bet_stars": bet_stars,
            "bet_ton": 0,
            "result_sector": result.index,
            "gift_won": result.gift,
            "balances": {
                "stars": user.balance_stars,
                "ton": str(user.balance_ton),
            }
        }