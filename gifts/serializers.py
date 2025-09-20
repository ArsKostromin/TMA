# serializers.py
from rest_framework import serializers
from gifts.models import Gift

class GiftSerializer(serializers.ModelSerializer):
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
            "symbol",
        ]


class InventorySerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True, read_only=True)

    class Meta:
        model = Gift._meta.get_field("user").related_model  # твоя User модель
        fields = ["id", "username", "gifts"]
