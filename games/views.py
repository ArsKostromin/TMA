import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from .serializers import (
    GameHistorySerializer,
    PublicGameHistorySerializer,
    PublicPvpGameSerializer,
    PvpGameDetailSerializer,
    TopPlayerSerializer,
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayRequestSerializer,
    SpinPlayResponseSerializer,
    LastWinnerSerializer,
)
from django.db.models import Sum, Count, Q
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model
from rest_framework import status
from django.db import transaction
from games.services.spin_service import SpinService
from .services.top_players import get_top_player 
from django.core.exceptions import ValidationError
from decimal import Decimal
from drf_spectacular.utils import extend_schema
from .services.last_winner import get_last_pvp_winner


User = get_user_model()

class GameHistoryView(ListAPIView):
    serializer_class = GameHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Game.objects.filter(players__user=user)
            .select_related("winner")
            .prefetch_related("players__gifts")
            .order_by("-started_at")[:20]
        )


class TopPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: TopPlayerSerializer},
        summary="Получение лучшего игрока",
        description="Возвращает игрока с наибольшим общим выигрышем в TON"
    )
    def get(self, request):
        top_player = get_top_player()
        if not top_player:
            return Response({"detail": "Нет игроков с победами"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TopPlayerSerializer(top_player)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PvPGameHistoryAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicPvpGameSerializer

    def get_queryset(self):
        return (
            Game.objects
            .filter(mode="pvp", status="finished")
            .select_related("winner")
            .prefetch_related("players__gifts", "players")
            .order_by("-started_at")
        )


class PvpGameDetailView(APIView):
    """Детальная информация о PVP игре по ID."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, game_id):
        try:
            game = (
                Game.objects
                .filter(id=game_id, mode="pvp", status="finished")
                .select_related("winner")
                .prefetch_related("players__gifts", "players")
                .get()
            )
        except Game.DoesNotExist:
            return Response(
                {"detail": "Игра не найдена"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PvpGameDetailSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpinPlayView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SpinPlayRequestSerializer,
        responses=SpinPlayResponseSerializer
    )
    def post(self, request):
        serializer = SpinPlayRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        bet_stars = data.get("bet_stars", 0)
        bet_ton = data.get("bet_ton", Decimal("0"))

        try:
            # Играем через SpinService
            game, result = SpinService.play(user, bet_stars, bet_ton)
            
            # Списываем балансы
            if bet_stars > 0:
                user.subtract_stars(bet_stars)
            if bet_ton > 0:
                user.subtract_ton(bet_ton)

            response_data = {
                "game_id": game.id,
                "bet_stars": bet_stars,
                "bet_ton": str(bet_ton),
                "result_sector": result.index,
                "gift_won": {
                    "id": result.gift.id,
                    "name": result.gift.name,
                    "image_url": result.gift.image_url,
                    "price_ton": str(result.gift.price_ton),
                    "rarity": result.gift.rarity,
                } if result.gift else None,
                "balances": {
                    "stars": user.balance_stars,
                    "ton": str(user.balance_ton),
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            

class SpinWheelView(APIView):
    """
    Получение всех секторов колеса для спина
    """
    
    @extend_schema(
        summary="Get all spin wheel sectors",
        responses={200: SpinWheelSectorSerializer(many=True)}
    )
    def get(self, request):
        # Берём все сектора, сортируя по индексу
        sectors = SpinWheelSector.objects.select_related("gift").all().order_by("index")
        serializer = SpinWheelSectorSerializer(sectors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpinGameHistoryView(ListAPIView):
    serializer_class = SpinGameHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            SpinGame.objects
            .filter(player=self.request.user)
            .select_related("gift_won")
            .order_by("-played_at")
        )

class LastPvpWinnerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        last_game, winner_gp = get_last_pvp_winner()

        if not last_game or not winner_gp:
            return Response({"detail": "Нет завершённых игр"}, status=404)

        data = LastWinnerSerializer(winner_gp).data
        data["game_id"] = last_game.id
        return Response(data)