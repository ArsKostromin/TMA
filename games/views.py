import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from .serializers import (
    GameHistorySerializer,
    PublicGameHistorySerializer,
    TopPlayerSerializer,
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayRequestSerializer,
    SpinPlayResponseSerializer,
)
from django.db.models import Sum, Count, Q
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model
from rest_framework import status
from django.db import transaction
from games.services.spin_service import SpinService
from .services.top_players import get_top_players 
from django.core.exceptions import ValidationError
from decimal import Decimal
from drf_spectacular.utils import extend_schema

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


class TopPlayersAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TopPlayerSerializer  

    def get_queryset(self):
        return get_top_players()


class PvPGameHistoryAPIView(ListAPIView):
    serializer_class = PublicGameHistorySerializer

    def get_queryset(self):
        return (
            Game.objects.filter(mode="pvp", status="finished")
            .order_by("-ended_at")[:10]
        )


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

        # логика игры
        user = request.user
        bet_stars = data.get("bet_stars", 0)
        bet_ton = data.get("bet_ton", Decimal("0"))
        # SpinService.play(...) и списание баланса

        response_data = {
            "game_id": 123,
            "bet_stars": bet_stars,
            "bet_ton": str(bet_ton),
            "result_sector": "Cherry",
            "gift_won": None,
            "balances": {
                "stars": user.balance_stars,
                "ton": str(user.balance_ton),
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)


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