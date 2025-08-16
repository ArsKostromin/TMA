from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Game, GamePlayer, SpinGame
from .serializers import GameHistorySerializer, SpinGameHistorySerializer, PublicGameHistorySerializer, TopPlayerSerializer
from django.db.models import Sum, Count, Q
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model

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