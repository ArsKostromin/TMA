# serializers.py
import logging
from rest_framework import serializers
from decimal import Decimal
from gifts.models import Gift

logger = logging.getLogger(__name__)

class GiftSerializer(serializers.ModelSerializer):
    # для вывода во фронт
    backdrop_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    image_url = serializers.SerializerMethodField()  # <-- теперь вычисляется

    class Meta:
        model = Gift
        fields = [
            "id",
            "user_username",
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

    def get_image_url(self, obj):
        """
        Если есть symbol — формируем ссылку вида:
        https://nft.fragment.com/gift/{symbol}.medium.jpg
        иначе — возвращаем то, что в базе.
        """
        if obj.symbol:
            return f"https://nft.fragment.com/gift/{obj.symbol}.medium.jpg"
        return obj.image_url

class GiftWithdrawSerializer(serializers.Serializer):
    # для вывода пользователю на аккаунт
    gift_id = serializers.IntegerField(required=True, help_text="ID подарка, который нужно вывести")

    def validate_gift_id(self, value):
        logger.debug(f"[GiftWithdrawSerializer] Проверка наличия подарка с ID={value}")
        if not Gift.objects.filter(id=value).exists():
            raise serializers.ValidationError("Подарок с таким ID не найден.")
        return value


class GiftAddSerializer(serializers.ModelSerializer):
    # для создания(пополнения) нового нфт
    backdrop_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Gift
        fields = [
            "id",
            "user_username",
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

            # 👇 добавляем сюда нужные поля для Telethon
            "peer_id",
            "msg_id",
            "access_hash",
            "sender_id",
            "chat_name",
        ]

    def validate_price_ton(self, value):
        return validate_price_ton(value)

    def create(self, validated_data):
        return create_gift_instance(validated_data, self.context)