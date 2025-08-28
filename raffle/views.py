from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.generics import RetrieveAPIView

from .serializers import CurrentRaffleSerializer
from .services import get_current_raffle_with_stats


class CurrentRaffleView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CurrentRaffleSerializer

    def get_object(self):
        raffle = get_current_raffle_with_stats(self.request.user)
        if raffle is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Нет активного розыгрыша")
        return raffle

    @extend_schema(
        summary="Текущий активный розыгрыш",
        description="Возвращает данные об активном розыгрыше и статус участия текущего пользователя.",
        responses={
            200: OpenApiResponse(response=CurrentRaffleSerializer, description="Успешный ответ"),
            404: OpenApiResponse(description="Нет активного розыгрыша"),
        },
        tags=["Raffle"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)