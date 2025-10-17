import logging
from decimal import Decimal
from rest_framework import serializers
from gifts.models import Gift

logger = logging.getLogger(__name__)


def validate_price_ton(value):
    logger.debug(f"[GiftValidator] Проверка price_ton: {value}")
    if value is None:
        return value
    try:
        return Decimal(str(value))
    except Exception:
        raise serializers.ValidationError("Некорректное значение price_ton")


def create_gift_instance(validated_data, context):
    """Создание или обновление подарка (используется в GiftAddSerializer)"""
    logger.info(f"[GiftValidator] Создание/обновление подарка: {validated_data}")

    backdrop_name = validated_data.pop("backdrop_name", None)
    if backdrop_name:
        validated_data["backdrop"] = backdrop_name
        logger.debug(f"[GiftValidator] backdrop_name мэппится в backdrop: {backdrop_name}")

    user_id = validated_data.pop("user", None)
    if user_id:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(telegram_id=user_id)
            validated_data["user"] = user
            logger.debug(f"[GiftValidator] Пользователь найден: {user_id}")
        except User.DoesNotExist:
            logger.warning(f"[GiftValidator] ❌ Пользователь с ID {user_id} не найден")
            raise serializers.ValidationError(f"Пользователь с ID {user_id} не найден")
    else:
        request = context.get("request")
        current_user = getattr(request, "user", None)
        if current_user and current_user.is_authenticated:
            validated_data["user"] = current_user
            logger.debug(f"[GiftValidator] Пользователь из request.user: {current_user.id}")
        else:
            logger.warning("[GiftValidator] ❌ Пользователь не аутентифицирован")

    ton_contract_address = validated_data.get("ton_contract_address")
    defaults = {k: v for k, v in validated_data.items() if k != "ton_contract_address"}

    gift, created = Gift.objects.update_or_create(
        ton_contract_address=ton_contract_address,
        defaults=defaults,
    )

    logger.info(f"[GiftValidator] {'Создан' if created else 'Обновлён'} подарок: {gift.ton_contract_address}")
    return gift
