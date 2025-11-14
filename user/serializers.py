from rest_framework import serializers
from django.conf import settings


class TelegramAuthRequestSerializer(serializers.Serializer):
    initData = serializers.CharField(required=True)


class TelegramAuthResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()
    access = serializers.CharField()
    refresh = serializers.CharField()

    def get_avatar_url(self, obj):
        """Возвращает аватарку пользователя или аватарку по умолчанию"""
        # obj здесь - это словарь из TelegramAuthService, где avatar_url уже получен через user.get_avatar_url()
        return obj.get('avatar_url') or getattr(settings, 'DEFAULT_AVATAR_URL', "https://teststudiaorbita.ru/media/avatars/diamond.png")


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class RefreshTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class UserBalanceSerializer(serializers.Serializer):
    balance_ton = serializers.DecimalField(max_digits=18, decimal_places=6)
    balance_stars = serializers.IntegerField()
    gift_count = serializers.IntegerField()
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        user = self.context['request'].user
        return user.get_avatar_url()


class CreateStarsInvoiceSerializer(serializers.Serializer):
    amount_stars = serializers.IntegerField(min_value=1)

    def validate_amount_stars(self, value):
        if value < 1:
            raise serializers.ValidationError("Минимальная ставка — 1 Star")
        return value


class CreateStarsInvoiceResponseSerializer(serializers.Serializer):
    invoice_link = serializers.CharField()
