# gifts/services/withdrawal_request.py
import logging
from django.db import transaction
from rest_framework import status
from gifts.models import Gift
from gifts.utils.telegram_payments import create_stars_invoice

logger = logging.getLogger(__name__)


class GiftWithdrawalRequestService:
    """
    Сервис для обработки запросов на вывод NFT-подарков.
    Работает без изменения модели - использует существующую структуру.
    """

    @staticmethod
    @transaction.atomic
    def create_withdrawal_request(user, gift_id: int):
        """
        Создает запрос на вывод подарка с проверкой принадлежности.
        Возвращает данные для оплаты.
        """
        logger.info(f"[GiftWithdrawalRequestService] 🔍 Создание запроса на вывод NFT ID={gift_id} пользователем {user.id}")

        try:
            gift = Gift.objects.select_for_update().get(id=gift_id)
        except Gift.DoesNotExist:
            logger.warning(f"[GiftWithdrawalRequestService] ❌ Подарок ID={gift_id} не найден")
            return {
                "status": status.HTTP_404_NOT_FOUND,
                "detail": "Подарок не найден."
            }

        # Проверяем принадлежность подарка
        if gift.user != user:
            logger.warning(f"[GiftWithdrawalRequestService] 🚫 Подарок ID={gift_id} не принадлежит пользователю {user.id}")
            return {
                "status": status.HTTP_403_FORBIDDEN,
                "detail": "Этот подарок вам не принадлежит."
            }

        # Создаем инвойс на оплату
        invoice_result = create_stars_invoice(user, gift_id, amount=25)
        
        if not invoice_result.get("ok"):
            logger.error(f"[GiftWithdrawalRequestService] 💀 Не удалось создать инвойс: {invoice_result.get('error')}")
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Ошибка при создании инвойса: {invoice_result.get('error')}"
            }

        logger.info(f"[GiftWithdrawalRequestService] ✅ Запрос на вывод создан для подарка {gift.name}")
        
        return {
            "status": status.HTTP_200_OK,
            "detail": "Запрос на вывод создан. Оплатите 25⭐ для завершения вывода.",
            "data": {
                "invoice_id": invoice_result.get("invoice_id"),
                "pay_url": invoice_result.get("pay_url"),
                "gift_info": {
                    "id": gift.id,
                    "name": gift.name,
                    "ton_contract_address": gift.ton_contract_address,
                    "image_url": gift.image_url
                },
                "amount_stars": 25,
                "payload": invoice_result.get("payload")
            }
        }

    @staticmethod
    @transaction.atomic
    def process_successful_payment(invoice_payload: str):
        """
        Обрабатывает успешную оплату и выполняет реальный вывод подарка.
        """
        logger.info(f"[GiftWithdrawalRequestService] 💳 Обработка успешной оплаты: {invoice_payload}")
        
        try:
            # Извлекаем gift_id из payload (формат: withdraw_gift_{gift_id})
            if not invoice_payload.startswith("withdraw_gift_"):
                logger.error(f"[GiftWithdrawalRequestService] ❌ Неверный формат payload: {invoice_payload}")
                return False
                
            gift_id = int(invoice_payload.replace("withdraw_gift_", ""))
            
            # Проверяем, что подарок существует
            try:
                gift = Gift.objects.get(id=gift_id)
            except Gift.DoesNotExist:
                logger.error(f"[GiftWithdrawalRequestService] ❌ Подарок ID={gift_id} не найден")
                return False
            
            # Выполняем реальный вывод подарка
            from gifts.services.withdrawal import GiftWithdrawalService
            withdrawal_result = GiftWithdrawalService.withdraw_gift(
                gift.user, 
                gift.id
            )
            
            if withdrawal_result["status"] == status.HTTP_200_OK:
                logger.info(f"[GiftWithdrawalRequestService] ✅ Вывод подарка завершен: {gift.name}")
                return True
            else:
                logger.error(f"[GiftWithdrawalRequestService] ❌ Ошибка при выводе подарка: {withdrawal_result}")
                return False
                
        except Exception as e:
            logger.exception(f"[GiftWithdrawalRequestService] ❌ Ошибка при обработке платежа: {e}")
            return False
