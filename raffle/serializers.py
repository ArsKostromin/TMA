from rest_framework import serializers
from gifts.serializers import GiftSerializer


# class GiftShortSerializer(serializers.Serializer):
#     id = serializers.IntegerField(allow_null=True)
#     ton_contract_address = serializers.CharField(allow_null=True)
#     name = serializers.CharField(allow_null=True)
#     image_url = serializers.URLField(allow_null=True)
#     price_ton = serializers.DecimalField(allow_null=True)
#     backdrop = serializers.URLField(allow_null=True)
#     symbol = serializers.CharField(allow_null=True)
#     price_ton = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
#     backdrop = serializers.URLField(allow_null=True)
#     symbol = serializers.CharField(allow_null=True)


class CurrentRaffleSerializer(serializers.Serializer):
    status = serializers.CharField()
    gift = GiftSerializer(allow_null=True)
    participants_count = serializers.IntegerField()
    started_at = serializers.DateTimeField(allow_null=True)
    ends_at = serializers.DateTimeField(allow_null=True)
    user_participates = serializers.BooleanField()

    def to_representation(self, instance):
        participants_count = getattr(instance, "participants_count", None)
        if participants_count is None:
            participants_count = instance.participants.count()

        user_participates = getattr(instance, "user_participates", False)

        return {
            "status": instance.status,
            "gift": GiftSerializer(getattr(instance, "prize", None)).data 
            if getattr(instance, "prize", None) else None,
            "participants_count": int(participants_count),
            "started_at": instance.started_at,
            "ends_at": instance.ends_at,
            "user_participates": bool(user_participates),
        }