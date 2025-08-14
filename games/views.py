from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Game, GamePlayer, SpinGame
from .serializers import GameHistorySerializer, SpinGameHistorySerializer


class GameHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # PVP / Daily / прочее
        games = Game.objects.filter(players__user=user)\
            .select_related("winner")\
            .prefetch_related("players__gifts")\
            .order_by("-started_at")[:20]

        spin_games = SpinGame.objects.filter(player=user)\
            .select_related("gift_won")\
            .order_by("-played_at")[:20]

        return Response({
            "games": GameHistorySerializer(games, many=True, context={"request": request}).data,
            "spin_games": SpinGameHistorySerializer(spin_games, many=True).data
        })
