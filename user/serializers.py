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
        if obj.get('avatar_url'):
            return obj['avatar_url']
        return getattr(settings, 'DEFAULT_AVATAR_URL', "https://teststudiaorbita.ru/media/avatars/diamond.png")


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class RefreshTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class UserBalanceSerializer(serializers.Serializer):
    balance_ton = serializers.DecimalField(max_digits=18, decimal_places=6)
    balance_stars = serializers.IntegerField()
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        """Возвращает аватарку пользователя или аватарку по умолчанию"""
        user = self.context['request'].user
        return user.get_avatar_url()

    def get_gift_count(self, obj):
        """Возвращает количество предметов в инвентаре пользователя"""
        user = self.context['request'].user
        return user.gifts.count()