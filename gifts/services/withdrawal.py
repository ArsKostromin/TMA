# gifts/services/withdrawal.py
import logging
from django.db import transaction
from rest_framework import status
from gifts.models import Gift

logger = logging.getLogger(__name__)


class GiftWithdrawalService:
    """
    Сервис для обработки вывода NFT-подарков.
    """

    @staticmethod
    @transaction.atomic
    def withdraw_gift(user, gift_id: int):
        """
        Проверяет принадлежность подарка пользователю и удаляет его из БД.
        """
        logger.info(f"[GiftWithdrawalService] 🔍 Попытка вывода NFT ID={gift_id} пользователем {user.id}")

        try:
            gift = Gift.objects.select_for_update().get(id=gift_id)
        except Gift.DoesNotExist:
            logger.warning(f"[GiftWithdrawalService] ❌ Подарок ID={gift_id} не найден")
            return {
                "status": status.HTTP_404_NOT_FOUND,
                "detail": "Подарок не найден."
            }

        if gift.user != user:
            logger.warning(f"[GiftWithdrawalService] 🚫 Подарок ID={gift_id} не принадлежит пользователю {user.id}")
            return {
                "status": status.HTTP_403_FORBIDDEN,
                "detail": "Этот подарок вам не принадлежит."
            }

        # Здесь может быть логика отправки NFT в блокчейн
        # send_to_ton_wallet(user_wallet, gift.ton_contract_address)

        gift_name = gift.name
        gift_contract = gift.ton_contract_address
        gift.delete()

        logger.info(f"[GiftWithdrawalService] ✅ Успешный вывод NFT {gift_name} ({gift_contract}) пользователем {user.id}")
        return {
            "status": status.HTTP_200_OK,
            "detail": f"Подарок {gift_name} ({gift_contract}) успешно выведен и удалён из базы."
        }
