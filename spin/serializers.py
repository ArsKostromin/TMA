from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from gifts.models import Gift
from django.contrib.auth import get_user_model
from django.db.models import Sum
from decimal import Decimal
from gifts.serializers import GiftSerializer


User = get_user_model()

class SpinWheelSectorSerializer(serializers.ModelSerializer):
    gift = GiftSerializer()

    class Meta:
        model = SpinWheelSector
        fields = [
            "index",
            "probability",
            "gift",
        ]


class SpinGameHistorySerializer(serializers.ModelSerializer):
    gift_won = GiftSerializer(read_only=True)

    class Meta:
        model = SpinGame
        fields = [
            "id",
            "bet_stars",
            "bet_ton",
            "win_amount",
            "gift_won",
            "result_sector",
            "played_at",
        ]


class SpinPlayRequestSerializer(serializers.Serializer):
    bet_stars = serializers.IntegerField(required=False, min_value=0, default=0)
    bet_ton = serializers.DecimalField(
        required=False, max_digits=18, decimal_places=6, min_value=0, default=Decimal("0")
    )


class SpinPlayResponseSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()
    bet_stars = serializers.IntegerField()
    bet_ton = serializers.CharField()
    payment_required = serializers.BooleanField()
    message = serializers.CharField(required=False)
    result_sector = serializers.IntegerField(allow_null=True, required=False)
    gift_won = serializers.DictField(allow_null=True, required=False)
    balances = serializers.DictField(child=serializers.CharField(), required=False)


