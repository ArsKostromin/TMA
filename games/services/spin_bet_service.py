# games/services/spin_bet_service.py
import logging
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from games.models import SpinGame
from games.services.spin_service import SpinService
from games.services.telegram_stars import TelegramStarsService

logger = logging.getLogger(__name__)


class SpinBetService:
    """
    Сервис для обработки ставок в спин игру.
    Создаёт инвойсы для оплаты звёздами и обрабатывает ставки в TON.
    """
    
    @staticmethod
    def validate_user(user):
        """Проверяет, что у пользователя есть telegram_id"""
        if not user.telegram_id:
            raise ValidationError("У аккаунта не указан Telegram ID (telegram_id)")
    
    @staticmethod
    @transaction.atomic
    def create_bet_with_stars(user, bet_stars: int, bet_ton: Decimal) -> dict:
        """
        Создаёт ставку со звёздами и возвращает ссылку на оплату.
        
        Args:
            user: Пользователь
            bet_stars: Ставка в звёздах
            bet_ton: Ставка в TON (может быть 0)
        
        Returns:
            dict с данными для ответа API
        """
        # Проверяем пользователя
        SpinBetService.validate_user(user)
        
        # Создаём игру заранее (со статусом pending - result_sector = None)
        game = SpinGame.objects.create(
            player=user,
            bet_stars=bet_stars,
            bet_ton=bet_ton,
            result_sector=None,  # None означает, что игра еще не сыграна
        )
        
        # Создаём инвойс для оплаты звёздами (возвращает ссылку для Mini App)
        invoice_result = TelegramStarsService.create_invoice(
            order_id=game.id,
            amount_stars=bet_stars,
            title="Ставка в рулетку",
            description=f"Оплата участия в спин-игре. Ставка: {bet_stars}⭐"
        )
        
        if not invoice_result.get("ok"):
            # Если не удалось создать инвойс - удаляем игру
            game.delete()
            raise ValidationError(f"Не удалось создать инвойс: {invoice_result.get('error')}")
        
        return {
            "game_id": game.id,
            "payment_required": True,
            "payment_link": invoice_result.get("invoice_link"),
            "bet_stars": bet_stars,
            "bet_ton": str(bet_ton),
            "message": "Оплатите инвойс для запуска игры"
        }
    
    @staticmethod
    @transaction.atomic
    def create_bet_with_ton(user, bet_ton: Decimal) -> dict:
        """
        Создаёт ставку только в TON и сразу запускает игру.
        
        Args:
            user: Пользователь
            bet_ton: Ставка в TON
        
        Returns:
            dict с результатом игры
        """
        # Проверяем баланс TON
        if user.balance_ton < bet_ton:
            raise ValidationError("Недостаточно TON на балансе")
        
        # Списываем TON и играем
        user.subtract_ton(bet_ton)
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

