from rest_framework import serializers


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

    def to_representation(self, instance):
        gift = getattr(instance, "prize", None)
        gift_data = None
        if gift is not None:
            gift_data = {
                "tg_nft_id": getattr(gift, "tg_nft_id", None),
                "name": getattr(gift, "name", None),
                "rarity": getattr(gift, "rarity", None),
                "image_url": getattr(gift, "image_url", None),
                "price_ton": getattr(gift, "price_ton", None),
                "backdrop": getattr(gift, "backdrop", None),
                "symbol": getattr(gift, "symbol", None),
            }

        participants_count = getattr(instance, "participants_count", None)
        if participants_count is None:
            # fallback, если не пришла аннотация (не должно происходить)
            participants_count = instance.participants.count()

        user_participates = getattr(instance, "user_participates", False)

        return {
            "status": instance.status,
            "gift": gift_data,
            "participants_count": int(participants_count),
            "started_at": instance.started_at,
            "ends_at": instance.ends_at,
            "user_participates": bool(user_participates),
        }


