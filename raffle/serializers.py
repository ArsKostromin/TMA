from rest_framework import serializers

from .models import DailyRaffle


class GiftShortSerializer(serializers.Serializer):
    tg_nft_id = serializers.CharField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    rarity = serializers.CharField(allow_null=True)
    image_url = serializers.URLField(allow_null=True)
    price_ton = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    backdrop = serializers.URLField(allow_null=True)
    symbol = serializers.CharField(allow_null=True)


class CurrentRaffleSerializer(serializers.Serializer):
    status = serializers.CharField()
    gift = GiftShortSerializer(allow_null=True)
    participants_count = serializers.IntegerField()
    started_at = serializers.DateTimeField(allow_null=True)
    ends_at = serializers.DateTimeField(allow_null=True)
    user_participates = serializers.BooleanField()

    @staticmethod
    def from_instance(raffle: DailyRaffle, *, user_participates: bool, participants_count: int):
        gift = raffle.prize
        gift_data = None
        if gift is not None:
            gift_data = {
                "tg_nft_id": gift.tg_nft_id,
                "name": gift.name,
                "rarity": gift.rarity,
                "image_url": gift.image_url,
                "price_ton": gift.price_ton,
                "backdrop": gift.backdrop,
                "symbol": gift.symbol,
            }

        data = {
            "status": raffle.status,
            "gift": gift_data,
            "participants_count": int(participants_count),
            "started_at": raffle.started_at,
            "ends_at": raffle.ends_at,
            "user_participates": bool(user_participates),
        }
        return CurrentRaffleSerializer(data)


