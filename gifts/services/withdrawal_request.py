# gifts/services/withdrawal_request.py
import logging
from django.db import transaction
from rest_framework import status
from gifts.models import Gift
from gifts.services.userbot_client import send_gift_via_userbot

logger = logging.getLogger(__name__)


class GiftWithdrawalRequestService:
    """
    Сервис для обработки запросов на вывод NFT-подарков.
    Отправляет подарок реально через userbot. Комиссия оплачивается реальными звёздами 
    с аккаунта userbot в Telegram (не из БД).
    """

    @staticmethod
    @transaction.atomic
    def create_withdrawal_request(user, gift_id: int):
        """
        Создает запрос на вывод подарка и отправляет его реально через userbot.
        Комиссия списывается реальными звёздами с аккаунта userbot в Telegram.
        Возвращает результат операции.
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

        # Проверяем наличие telegram_id у пользователя
        recipient_telegram_id = getattr(user, "telegram_id", None)
        if not recipient_telegram_id:
            logger.error(f"[GiftWithdrawalRequestService] 🚫 У пользователя {user.id} отсутствует telegram_id")
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "detail": "У аккаунта не указан Telegram ID (telegram_id)."
            }

        # Получаем ton_contract_address для поиска подарка в инвентаре userbot
        # Поиск по slug работает даже для выигранных подарков, где msg_id может отсутствовать
        # Преобразуем в строку, так как может быть числом в БД
        try:
            ton_contract_address_raw = gift.ton_contract_address
            ton_contract_address = str(ton_contract_address_raw) if ton_contract_address_raw else None
            logger.info(f"[GiftWithdrawalRequestService] 📋 Данные подарка: id={gift_id}, name={gift.name}, ton_contract_address={ton_contract_address} (тип в БД: {type(ton_contract_address_raw).__name__})")
        except Exception as e:
            logger.error(f"[GiftWithdrawalRequestService] ❌ Ошибка при получении ton_contract_address: {e}")
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Ошибка при получении данных подарка: {str(e)}"
            }
        
        if not ton_contract_address:
            logger.error(f"[GiftWithdrawalRequestService] ❌ У подарка ID={gift_id} отсутствует ton_contract_address")
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "detail": "У подарка отсутствует ton_contract_address, невозможно найти его в инвентаре."
            }
        
        # Отправляем подарок реально через userbot
        # Комиссия будет списана реальными звёздами с аккаунта userbot в Telegram
        logger.info(f"[GiftWithdrawalRequestService] 🚀 Отправка запроса в userbot: gift_id={gift_id}, recipient={recipient_telegram_id}, ton_contract_address={ton_contract_address}")
        send_result = send_gift_via_userbot(
            gift_id=gift_id,
            recipient_telegram_id=recipient_telegram_id,
            ton_contract_address=ton_contract_address
        )
        
        logger.info(f"[GiftWithdrawalRequestService] 📥 Ответ от userbot: {send_result}")

        if not send_result.get("ok"):
            logger.error(f"[GiftWithdrawalRequestService] ❌ Не удалось отправить подарок: {send_result.get('error')}")
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Ошибка при отправке подарка: {send_result.get('error', 'Неизвестная ошибка')}"
            }

        # Подарок успешно отправлен, удаляем его из БД
        gift_name = gift.name
        gift_contract = gift.ton_contract_address
        gift.delete()
        
        logger.info(f"[GiftWithdrawalRequestService] ✅ Подарок {gift_name} успешно отправлен и удален из БД")
        
        return {
            "status": status.HTTP_200_OK,
            "detail": f"Подарок {gift_name} успешно отправлен. Комиссия оплачена реальными звёздами с аккаунта userbot.",
            "data": {
                "gift_info": {
                    "id": gift_id,
                    "name": gift_name,
                    "ton_contract_address": gift_contract,
                },
                "sent": True
            }
        }

