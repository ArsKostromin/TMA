from rest_framework import serializers
from .models import Game, GamePlayer, SpinGame
from gifts.models import Gift


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
