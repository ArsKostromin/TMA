from rest_framework import serializers


class TelegramAuthRequestSerializer(serializers.Serializer):
    initData = serializers.CharField(required=True)


class TelegramAuthResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True)
    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class RefreshTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()