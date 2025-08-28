from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import DailyRaffle, DailyRaffleParticipant
from .serializers import CurrentRaffleSerializer


class CurrentRaffleView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        raffle = (
            DailyRaffle.objects.filter(status="active")
            .order_by("-started_at")
            .first()
        )

        if not raffle:
            return Response({"detail": "Нет активного розыгрыша"}, status=status.HTTP_404_NOT_FOUND)

        participants_count = raffle.participants.count()

        user_participates = False
        if request.user and request.user.is_authenticated:
            user_participates = DailyRaffleParticipant.objects.filter(
                raffle=raffle, user=request.user
            ).exists()

        serializer = CurrentRaffleSerializer.from_instance(
            raffle,
            user_participates=user_participates,
            participants_count=participants_count,
        )
        return Response(serializer.data)
