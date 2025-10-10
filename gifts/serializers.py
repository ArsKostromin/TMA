# serializers.py
from rest_framework import serializers
from decimal import Decimal
from gifts.models import Gift

class GiftSerializer(serializers.ModelSerializer):
    # Доп. поля из входящих данных, которые нужно смэппить
    backdrop_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Gift
        fields = [
            "id",
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
            # write-only поле для удобства мэппинга
            "backdrop_name",
        ]

    def validate_price_ton(self, value):
        if value is None:
            return value
        # Приводим к Decimal для согласованности хранения
        try:
            return Decimal(str(value))
        except Exception:
            raise serializers.ValidationError("Некорректное значение price_ton")

    def create(self, validated_data):
        # Мэппим backdrop_name -> backdrop, если прислали оба — приоритет у backdrop_name
        backdrop_name = validated_data.pop("backdrop_name", None)
        if backdrop_name:
            validated_data["backdrop"] = backdrop_name

        # Владелец — текущий пользователь
        request = self.context.get("request")
        current_user = getattr(request, "user", None)

        # Обеспечим наличие владельца, если он есть в контексте
        if current_user and current_user.is_authenticated:
            validated_data["user"] = current_user

        # Upsert по ton_contract_address (уникальный)
        ton_contract_address = validated_data.get("ton_contract_address")
        defaults = {k: v for k, v in validated_data.items() if k != "ton_contract_address"}

        gift, _created = Gift.objects.update_or_create(
            ton_contract_address=ton_contract_address,
            defaults=defaults,
        )
        return gift


class InventorySerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True, read_only=True)

    class Meta:
        model = Gift._meta.get_field("user").related_model  # твоя User модель
        fields = ["id", "username", "gifts"]
