from rest_framework import serializers
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from gifts.models import Gift
from django.contrib.auth import get_user_model

User = get_user_model()

class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = ["id", "name", "image_url"]


class GamePlayerSerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True)

    class Meta:
        model = GamePlayer
        fields = ["bet_ton", "bet_stars", "chance_percent", "gifts"]


class GameHistorySerializer(serializers.ModelSerializer):
    player_data = serializers.SerializerMethodField()
    is_winner = serializers.SerializerMethodField()
    winner_id = serializers.IntegerField(source="winner.id", read_only=True)

    class Meta:
        model = Game
        fields = [
            "id", "mode", "status", "pot_amount_ton", "pot_amount_stars",
            "started_at", "ended_at", "winner_id", "is_winner", "player_data"
        ]

    def get_player_data(self, obj):
        user = self.context["request"].user
        gp = obj.players.filter(user=user).first()
        return GamePlayerSerializer(gp).data if gp else None

    def get_is_winner(self, obj):
        return obj.winner_id == self.context["request"].user.id


class SpinGameHistorySerializer(serializers.ModelSerializer):
    gift_won = GiftSerializer()

    class Meta:
        model = SpinGame
        fields = [
            "id", "sectors_count", "bet_ton", "bet_stars",
            "result_sector", "gift_won", "played_at"
        ]


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = ["id", "name", "image_url"]


class GamePlayerSerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True)

    class Meta:
        model = GamePlayer
        fields = ["user", "bet_ton", "bet_stars", "chance_percent", "gifts"]


class PublicGameHistorySerializer(serializers.ModelSerializer):
    players = GamePlayerSerializer(many=True, read_only=True)
    winner_id = serializers.IntegerField(source="winner.id", read_only=True)

    class Meta:
        model = Game
        fields = [
            "id", "mode", "status", "pot_amount_ton", "pot_amount_stars",
            "started_at", "ended_at", "winner_id", "players"
        ]


class TopPlayerSerializer(serializers.ModelSerializer):
    wins_count = serializers.IntegerField()
    total_wins_ton = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_wins_stars = serializers.IntegerField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "avatar_url",   # берём прямо из модели User
            "wins_count",
            "total_wins_ton",
            "total_wins_stars",
        ]


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = [
            "id",
            "name",
            "description",
            "image_url",
            "price_ton",
            "rarity",
        ]


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