from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.generics import RetrieveAPIView

from .serializers import CurrentRaffleSerializer
from .services import get_current_raffle_with_stats
from .services.join_raffle import join_current_raffle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


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


class JoinRaffleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Вступить в текущий розыгрыш",
        description="Проверяет участие пользователя в играх за 24 часа и добавляет в розыгрыш.",
        responses={
            201: OpenApiResponse(description="Успешно добавлен"),
            204: OpenApiResponse(description="Уже участвует"),
            403: OpenApiResponse(description="Не выполнено условие участия"),
            404: OpenApiResponse(description="Нет активного розыгрыша"),
        },
        tags=["Raffle"],
    )
    def post(self, request):
        code, _ = join_current_raffle(request.user)
        if code == "no_active":
            return Response({"detail": "Нет активного розыгрыша"}, status=status.HTTP_404_NOT_FOUND)
        if code == "forbidden":
            return Response({"detail": "Нужно сыграть в игру за последние 24 часа"}, status=status.HTTP_403_FORBIDDEN)
        if code == "conflict":
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_201_CREATED)