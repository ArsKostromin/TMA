import logging
from django.db import transaction
from rest_framework import status
from gifts.models import Gift
# Мы предполагаем, что GiftWithdrawalService и необходимые импорты существуют.
from gifts.services.withdrawal import GiftWithdrawalService 
# Удален импорт create_star_invoice_via_userbot, так как мы пропускаем этот шаг.

logger = logging.getLogger(__name__)


class GiftWithdrawalRequestService:
    """
    Сервис для обработки запросов на вывод NFT-подарков.
    Теперь выполняет немедленный вывод, используя Stars Userbot-аккаунта для покрытия комиссии.
    """

    @staticmethod
    @transaction.atomic
    def create_withdrawal_request(user, gift_id: int):
        """
        Создает запрос на вывод подарка и немедленно запускает вывод.
        Комиссия оплачивается со счета Userbot.
        """
        logger.info(f" 🔍 Немедленный вывод NFT ID={gift_id} пользователем {user.id}")

        try:
            gift = Gift.objects.select_for_update().get(id=gift_id)
        except Gift.DoesNotExist:
            logger.warning(f" ❌ Подарок ID={gift_id} не найден")
            return {
                "status": status.HTTP_404_NOT_FOUND,
                "detail": "Подарок не найден."
            }

        # Проверяем принадлежность подарка
        if gift.user!= user:
            logger.warning(f" 🚫 Подарок ID={gift_id} не принадлежит пользователю {user.id}")
            return {
                "status": status.HTTP_403_FORBIDDEN,
                "detail": "Этот подарок вам не принадлежит."
            }
        
        # --- НОВЫЙ ПОТОК: НЕМЕДЛЕННЫЙ ВЫВОД ---
        # 1. Запускаем сервис финального вывода.
        # Этот сервис должен вызвать ваш Userbot API /send_gift, 
        # который автоматически оплатит необходимую комиссию Stars'ами.
        
        try:
            withdrawal_result = GiftWithdrawalService.withdraw_gift(
                gift.user, 
                gift.id
            )

            if withdrawal_result.get("status") == status.HTTP_200_OK:
                logger.info(f" ✅ Вывод подарка завершен: {gift.name}. Оплачено Userbot.")
                return {
                    "status": status.HTTP_200_OK,
                    "detail": "Подарок успешно отправлен. Комиссия покрыта со счета Userbot.",
                    "data": {
                        "gift_info": {
                            "id": gift.id,
                            "name": gift.name,
                            "ton_contract_address": gift.ton_contract_address,
                            "image_url": gift.image_url
                        },
                        "withdrawal_status": "SENT",
                        "transaction_details": withdrawal_result.get("data")
                    }
                }
            else:
                logger.error(f" ❌ Ошибка при выводе подарка: {withdrawal_result.get('error')}")
                # Это может быть ошибка STARGIFT_NOT_FOUND или недостаток XTR на балансе юзербота
                return {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": f"Ошибка при автоматическом выводе: {withdrawal_result.get('error')}"
                }

        except Exception as e:
            logger.exception(f" ❌ Критическая ошибка при немедленном выводе: {e}")
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Критическая ошибка сервера при выполнении вывода."
            }
        # --- КОНЕЦ НОВОГО ПОТОКА ---

    @staticmethod
    @transaction.atomic
    def process_successful_payment(invoice_payload: str):
        """
        [Устарело в новом потоке] Обрабатывает успешную оплату.
        Эта функция больше не должна вызываться, если вы пропускаете инвойс.
        """
        logger.warning(f" ⚠️ ОБРАБОТКА WEBHOOK: Payment webhook получен, но инвойс пропущен. {invoice_payload}")
        return False # Возвращаем False, так как этот инвойс не должен был быть создан.