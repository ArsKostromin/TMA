# serializers.py
import logging
from rest_framework import serializers
from decimal import Decimal
from gifts.models import Gift
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class GiftSerializer(serializers.ModelSerializer):
    backdrop_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Gift
        fields = [
            "id",
            "user",
            "ton_contract_address",
            "name",
            "image_url",
            "price_ton",
            "backdrop",
            "symbol",
            "model_name",
            "pattern_name",
            "model_rarity_permille",
            "pattern_rarity_permille",
            "backdrop_rarity_permille",
            "model_original_details",
            "pattern_original_details",
            "backdrop_original_details",
            "rarity_level",
            "backdrop_name",
        ]

    def validate_price_ton(self, value):
        logger.debug(f"[GiftSerializer] Проверка price_ton: {value}")
        if value is None:
            return value
        try:
            return Decimal(str(value))
        except Exception:
            raise serializers.ValidationError("Некорректное значение price_ton")

    def create(self, validated_data):
        logger.info(f"[GiftSerializer] Создание/обновление подарка: {validated_data}")

        backdrop_name = validated_data.pop("backdrop_name", None)
        if backdrop_name:
            validated_data["backdrop"] = backdrop_name
            logger.debug(f"[GiftSerializer] backdrop_name мэппится в backdrop: {backdrop_name}")

        user_id = validated_data.pop("user", None)
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(telegram_id=user_id)
                validated_data["user"] = user
                logger.debug(f"[GiftSerializer] Пользователь найден: {user_id}")
            except User.DoesNotExist:
                logger.warning(f"[GiftSerializer] ❌ Пользователь с ID {user_id} не найден")
                raise serializers.ValidationError(f"Пользователь с ID {user_id} не найден")
        else:
            request = self.context.get("request")
            current_user = getattr(request, "user", None)
            if current_user and current_user.is_authenticated:
                validated_data["user"] = current_user
                logger.debug(f"[GiftSerializer] Пользователь из request.user: {current_user.id}")
            else:
                logger.warning("[GiftSerializer] ❌ Пользователь не аутентифицирован")

        ton_contract_address = validated_data.get("ton_contract_address")
        defaults = {k: v for k, v in validated_data.items() if k != "ton_contract_address"}

        gift, created = Gift.objects.update_or_create(
            ton_contract_address=ton_contract_address,
            defaults=defaults,
        )

        logger.info(f"[GiftSerializer] {'Создан' if created else 'Обновлён'} подарок: {gift.ton_contract_address}")
        return gift



class InventorySerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True, read_only=True)

    class Meta:
        model = Gift._meta.get_field("user").related_model  # твоя User модель
        fields = ["id", "username", "gifts"]


class WithdrawGiftRequestSerializer(serializers.Serializer):
    """
    Запрос на вывод (передачу) подарка на аккаунт пользователя в Telegram.
    По умолчанию использует аутентифицированного пользователя как получателя.
    """
    gift_contract_address = serializers.CharField(max_length=255)
    # опционально можно передать получателя (телеграм id) вручную
    to_telegram_id = serializers.IntegerField(required=False)
    # фиксированная комиссия (по требованию ТЗ: 25 звёзд)
    fee_stars = serializers.IntegerField(required=False, min_value=0, default=25)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Требуется аутентификация")

        # Если не передан to_telegram_id — берём из профиля пользователя
        to_tid = attrs.get("to_telegram_id")
        if to_tid is None:
            if not getattr(user, "telegram_id", None):
                raise serializers.ValidationError("У пользователя не задан telegram_id")
            attrs["to_telegram_id"] = int(user.telegram_id)

        # Проверяем владение подарком (по тон-идентификатору)
        gaddr = attrs["gift_contract_address"]
        try:
            gift = Gift.objects.get(ton_contract_address=gaddr, user=user)
        except Gift.DoesNotExist:
            raise serializers.ValidationError("Подарок не найден в вашем инвентаре")

        # Проверка Stars для комиссии
        fee = int(attrs.get("fee_stars", 25))
        if user.balance_stars < fee:
            raise serializers.ValidationError("Недостаточно Stars для комиссии")

        attrs["gift_instance"] = gift
        attrs["user_instance"] = user
        return attrs