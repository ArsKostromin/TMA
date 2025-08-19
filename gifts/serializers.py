# serializers.py
from rest_framework import serializers
from .models import Gift, Inventory


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = ["id", "name", "description", "image_url", "price_ton", "rarity"]


class InventorySerializer(serializers.ModelSerializer):
    gift = GiftSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "gift", "quantity", "acquired_at"]
