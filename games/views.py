import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from .serializers import GameHistorySerializer, SpinGameHistorySerializer, PublicGameHistorySerializer, TopPlayerSerializer, SpinWheelSectorSerializer
from django.db.models import Sum, Count, Q
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model
from rest_framework import status
from django.db import transaction
from gifts.models import Inventory
from games.services.spin_service import SpinService
from django.core.exceptions import ValidationError
from decimal import Decimal

User = get_user_model()

class GameHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # PVP / Daily / прочее
        games = Game.objects.filter(players__user=user)\
            .select_related("winner")\
            .prefetch_related("players__gifts")\
            .order_by("-started_at")[:20]

        # spin_games = SpinGame.objects.filter(player=user)\
        #     .select_related("gift_won")\
        #     .order_by("-played_at")[:20]

        return Response({
            "games": GameHistorySerializer(games, many=True, context={"request": request}).data,
        })


class TopPlayersAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        winners = (
            User.objects.annotate(
                total_wins_ton=Sum(
                    "games_won__pot_amount_ton",
                    filter=Q(games_won__status="finished", games_won__mode="pvp"),
                    default=0
                ),
                total_wins_stars=Sum(
                    "games_won__pot_amount_stars",
                    filter=Q(games_won__status="finished", games_won__mode="pvp"),
                    default=0
                ),
                wins_count=Count(
                    "games_won",
                    filter=Q(games_won__status="finished", games_won__mode="pvp")
                ),
            )
            .filter(wins_count__gt=0)
            .order_by("-total_wins_ton")[:20]
        )

        serializer = TopPlayerSerializer(winners, many=True)
        return Response(serializer.data)


class PvPGameHistoryAPIView(ListAPIView):
    serializer_class = PublicGameHistorySerializer

    def get_queryset(self):
        return (
            Game.objects.filter(mode="pvp", status="finished")
            .order_by("-ended_at")[:10]
        )


class SpinPlayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user: User = request.user
        bet_stars = request.data.get("bet_stars")
        bet_ton = request.data.get("bet_ton")

        try:
            # Приведение типов
            bet_stars = int(bet_stars) if bet_stars else 0
            bet_ton = Decimal(bet_ton) if bet_ton else Decimal("0")

            # Проверка средств до игры
            if bet_stars and user.balance_stars < bet_stars:
                return Response({"error": "Недостаточно Stars"}, status=status.HTTP_400_BAD_REQUEST)
            if bet_ton and user.balance_ton < bet_ton:
                return Response({"error": "Недостаточно TON"}, status=status.HTTP_400_BAD_REQUEST)

            # Запуск игры
            game, chosen = SpinService.play(user, bet_stars, bet_ton)

            # Списание средств
            if bet_stars:
                user.balance_stars -= bet_stars
            if bet_ton:
                user.balance_ton -= bet_ton
            user.save(update_fields=["balance_stars", "balance_ton"])

            return Response({
                "game_id": game.id,
                "bet_stars": game.bet_stars,
                "bet_ton": str(game.bet_ton),
                "result_sector": game.result_sector,
                "gift_won": game.gift_won.name if game.gift_won else None,
                "balances": {
                    "stars": user.balance_stars,
                    "ton": str(user.balance_ton),
                }
            })

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SpinWheelView(APIView):
    def get(self, request):
        sectors = SpinWheelSector.objects.select_related("gift").all().order_by("index")
        serializer = SpinWheelSectorSerializer(sectors, many=True)
        return Response({"wheel": serializer.data})