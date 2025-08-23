from rest_framework import serializers
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from gifts.models import Gift
from django.contrib.auth import get_user_model
from django.db.models import Sum
from decimal import Decimal

User = get_user_model()

class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = ["id", "name", "image_url"]


class GamePlayerSerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True)

    class Meta:
        model = GamePlayer
        fields = ["bet_ton", "chance_percent", "gifts"]


class GameHistorySerializer(serializers.ModelSerializer):
    player_data = serializers.SerializerMethodField()
    is_winner = serializers.SerializerMethodField()
    winner_id = serializers.IntegerField(source="winner.id", read_only=True)

    class Meta:
        model = Game
        fields = [
            "id", "mode", "status", "pot_amount_ton",
            "started_at", "ended_at", "winner_id", "is_winner", "player_data"
        ]

    def get_player_data(self, obj):
        user = self.context["request"].user
        gp = obj.players.filter(user=user).first()
        return GamePlayerSerializer(gp).data if gp else None

    def get_is_winner(self, obj):
        return obj.winner_id == self.context["request"].user.id


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = ["id", "name", "image_url"]


class GamePlayerSerializer(serializers.ModelSerializer):
    gifts = GiftSerializer(many=True)

    class Meta:
        model = GamePlayer
        fields = ["user", "bet_ton", "chance_percent", "gifts"]


class PublicGameHistorySerializer(serializers.ModelSerializer):
    players = GamePlayerSerializer(many=True, read_only=True)
    winner_id = serializers.IntegerField(source="winner.id", read_only=True)

    class Meta:
        model = Game
        fields = [
            "id", "mode", "status", "pot_amount_ton",
            "started_at", "ended_at", "winner_id", "players"
        ]


class TopPlayerSerializer(serializers.ModelSerializer):
    wins_count = serializers.SerializerMethodField()
    total_wins_ton = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "avatar_url",
            "wins_count",
            "total_wins_ton",
        ]

    def get_wins_count(self, obj):
        return obj.games_won.filter(status="finished", mode="pvp").count()

    def get_total_wins_ton(self, obj):
        return obj.games_won.filter(status="finished", mode="pvp").aggregate(
            total=Sum("pot_amount_ton")
        )["total"] or 0


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


class SpinPlayRequestSerializer(serializers.Serializer):
    bet_stars = serializers.IntegerField(required=False, min_value=0, default=0)
    bet_ton = serializers.DecimalField(
        required=False, max_digits=18, decimal_places=6, min_value=0, default=Decimal("0")
    )

class SpinPlayResponseSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()
    bet_stars = serializers.IntegerField()
    bet_ton = serializers.DecimalField(max_digits=18, decimal_places=6)
    result_sector = serializers.CharField()
    gift_won = serializers.CharField(allow_null=True)
    balances = serializers.DictField(child=serializers.CharField())


class LastWinnerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    avatar_url = serializers.CharField(source="user.avatar_url")
    win_amount = serializers.SerializerMethodField()

    class Meta:
        model = GamePlayer
        fields = [
            "id",
            "username",
            "avatar_url",
            "total_bet_ton",
            "chance_percent",
            "win_amount",
        ]

    def get_win_amount(self, obj):
        """Получить выигрыш игрока из игры"""
        game = obj.game
        if game and game.status == "finished":
            # Выигрыш = общая сумма в банке минус комиссия
            commission_amount = game.pot_amount_ton * (game.commission_percent / Decimal("100"))
            return str(game.pot_amount_ton - commission_amount)
        return "0"