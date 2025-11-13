from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Game, GamePlayer
from gifts.models import Gift
from django.contrib.auth import get_user_model
from django.db.models import Sum
from decimal import Decimal
from gifts.serializers import GiftSerializer


User = get_user_model()


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
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "avatar_url",
            "wins_count",
            "total_wins_ton",
        ]

    def get_avatar_url(self, obj):
        return obj.get_avatar_url()

    def get_wins_count(self, obj):
        return obj.games_won.filter(status="finished", mode="pvp").count()

    def get_total_wins_ton(self, obj):
        total = obj.games_won.filter(status="finished", mode="pvp").aggregate(
            total=Sum("pot_amount_ton")
        )["total"]
        return total or 0


class OnlinePlayersCountSerializer(serializers.Serializer):
    online_count = serializers.IntegerField()


class LastWinnerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    avatar_url = serializers.SerializerMethodField()
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

    def get_avatar_url(self, obj):
        """Возвращает аватарку пользователя или аватарку по умолчанию"""
        return obj.user.get_avatar_url()

    def get_win_amount(self, obj):
        """Получить выигрыш игрока из игры"""
        game = obj.game
        if game and game.status == "finished":
            # Выигрыш = общая сумма в банке минус комиссия
            commission_amount = game.pot_amount_ton * (game.commission_percent / Decimal("100"))
            return str(game.pot_amount_ton - commission_amount)
        return "0"


class PublicPvpGameSerializer(serializers.ModelSerializer):
    """Публичная карточка PVP игры с данными победителя и итогами."""

    hash = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    detail_url = serializers.SerializerMethodField()

    winner = serializers.SerializerMethodField()
    winner_gift_icons = serializers.SerializerMethodField()
    win_amount_ton = serializers.SerializerMethodField()
    winner_chance_percent = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "id",
            "hash",
            "started_at",
            "detail_url",
            "winner",
            "winner_gift_icons",
            "win_amount_ton",
            "winner_chance_percent",
        ]

    def _get_winner_gp(self, obj):
        """Вернуть объект GamePlayer победителя для игры."""
        if not obj.winner_id:
            return None
        return obj.players.filter(user_id=obj.winner_id).first()

    def get_detail_url(self, obj):
        request = self.context.get("request")
        try:
            return reverse("pvp-game-detail", args=[obj.id], request=request)
        except Exception:
            # Фолбэк на относительный путь, если нет request в контексте
            return f"/games/pvp-game/{obj.id}/"

    def get_winner(self, obj):
        user = obj.winner
        if not user:
            return None
        return {
            "id": user.id,
            "username": getattr(user, "username", None),
            "avatar_url": user.get_avatar_url(),
        }

    def get_winner_gift_icons(self, obj):
        gp = self._get_winner_gp(obj)
        if not gp:
            return []
        # показываем только иконки (image_url) подарков победителя
        return list(gp.gifts.values_list("image_url", flat=True))

    def get_win_amount_ton(self, obj):
        # Выигрыш = банк минус комиссия
        if obj.pot_amount_ton is None:
            return "0.00"
        commission_amount = obj.pot_amount_ton * (obj.commission_percent / Decimal("100"))
        win_amount = obj.pot_amount_ton - commission_amount
        # Форматируем до 2 знаков после запятой
        return f"{win_amount:.2f}"

    def get_winner_chance_percent(self, obj):
        gp = self._get_winner_gp(obj)
        if not gp or gp.chance_percent is None:
            return "0"
        return str(gp.chance_percent)


class WinnerGiftDetailSerializer(serializers.ModelSerializer):
    """Детальная информация о подарке победителя."""
    
    class Meta:
        model = Gift
        fields = [
            "id",
            "name", 
            "image_url",
            "price_ton",
        ]


class PvpGameDetailSerializer(serializers.ModelSerializer):
    """Детальная информация о PVP игре."""
    
    hash = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    ended_at = serializers.DateTimeField(read_only=True)
    
    winner = serializers.SerializerMethodField()
    winner_gifts = serializers.SerializerMethodField()
    win_amount_ton = serializers.SerializerMethodField()
    winner_chance_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            "id",
            "hash", 
            "started_at",
            "ended_at",
            "winner",
            "winner_gifts",
            "win_amount_ton",
            "winner_chance_percent",
        ]
    
    def _get_winner_gp(self, obj):
        """Вернуть объект GamePlayer победителя для игры."""
        if not obj.winner_id:
            return None
        return obj.players.filter(user_id=obj.winner_id).first()
    
    def get_winner(self, obj):
        user = obj.winner
        if not user:
            return None
        return {
            "id": user.id,
            "username": getattr(user, "username", None),
            "avatar_url": user.get_avatar_url(),
        }
    
    def get_winner_gifts(self, obj):
        """Получить все подарки победителя с деталями."""
        gp = self._get_winner_gp(obj)
        if not gp:
            return []
        return WinnerGiftDetailSerializer(gp.gifts.all(), many=True).data
    
    def get_win_amount_ton(self, obj):
        # Выигрыш = банк минус комиссия
        if obj.pot_amount_ton is None:
            return "0.00"
        commission_amount = obj.pot_amount_ton * (obj.commission_percent / Decimal("100"))
        win_amount = obj.pot_amount_ton - commission_amount
        # Форматируем до 2 знаков после запятой
        return f"{win_amount:.2f}"
    
    def get_winner_chance_percent(self, obj):
        gp = self._get_winner_gp(obj)
        if not gp or gp.chance_percent is None:
            return "0"
        return str(gp.chance_percent)