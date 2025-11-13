# games/services/spin_payment.py
import logging
from django.db import transaction
from rest_framework import status
from spin.models import SpinGame
from .spin_service import SpinService

logger = logging.getLogger(__name__)


class SpinPaymentService:
    """
    Сервис для обработки платежей за спин игры.
    Обрабатывает успешные платежи Telegram Stars и запускает игру.
    """
    
    @staticmethod
    @transaction.atomic
    def process_successful_payment(invoice_payload: str) -> bool:
        """
        Обрабатывает успешную оплату за спин игру и запускает игру.
        
        Args:
            invoice_payload: Payload из инвойса (формат: spin_game_{game_id})
        
        Returns:
            bool: True если игра успешно запущена, False в случае ошибки
        """
        logger.info(f"[SpinPaymentService] 💳 Обработка успешной оплаты: {invoice_payload}")
        
        try:
            # Извлекаем game_id из payload (формат: spin_game_{game_id})
            if not invoice_payload.startswith("spin_game_"):
                logger.error(f"[SpinPaymentService] ❌ Неверный формат payload: {invoice_payload}")
                return False
                
            game_id = int(invoice_payload.replace("spin_game_", ""))
            
            # Проверяем, что игра существует и еще не сыграна
            try:
                game = SpinGame.objects.select_for_update().get(
                    id=game_id,
                    result_sector__isnull=True  # Игра еще не сыграна
                )
            except SpinGame.DoesNotExist:
                logger.error(f"[SpinPaymentService] ❌ Игра ID={game_id} не найдена или уже сыграна")
                return False
            
            # Запускаем игру через SpinService
            # Передаём game_id чтобы использовать существующую игру
            # bet_stars уже оплачены через Telegram, не списываем
            updated_game, result = SpinService.play(
                user=game.player,
                bet_stars=game.bet_stars,
                bet_ton=game.bet_ton,
                game_id=game_id
            )
            
            logger.info(f"[SpinPaymentService] ✅ Игра ID={game_id} успешно запущена. Сектор: {result.index}")
            return True
                
        except Exception as e:
            logger.exception(f"[SpinPaymentService] ❌ Ошибка при обработке платежа: {e}")
            return False

