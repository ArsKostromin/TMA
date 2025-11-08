from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Game, GamePlayer, SpinGame, SpinWheelSector
from .serializers import (
    GameHistorySerializer,
    PublicPvpGameSerializer,
    PvpGameDetailSerializer,
    TopPlayerSerializer,
    SpinWheelSectorSerializer,
    SpinGameHistorySerializer,
    SpinPlayRequestSerializer,
    SpinPlayResponseSerializer,
    LastWinnerSerializer,
    OnlinePlayersCountSerializer,
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
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .services.last_winner import get_last_pvp_winner
from .services.game import GameService
from .api_examples import (
    GAME_HISTORY_EXAMPLE,
    TOP_PLAYER_EXAMPLE,
    PVP_GAME_HISTORY_EXAMPLE,
    PVP_GAME_DETAIL_EXAMPLE,
    SPIN_PLAY_REQUEST_EXAMPLE,
    SPIN_PLAY_RESPONSE_EXAMPLE,
    SPIN_WHEEL_EXAMPLE,
    SPIN_GAME_HISTORY_EXAMPLE,
    LAST_WINNER_EXAMPLE,
)


User = get_user_model()

class GameHistoryView(ListAPIView):
    serializer_class = GameHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="История игр пользователя",
        description="Возвращает последние 20 игр текущего пользователя с деталями ставок и подарков",
        responses={
            200: OpenApiResponse(
                response=GameHistorySerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=GAME_HISTORY_EXAMPLE
                    )
                ],
            ),
        },
        tags=["Games"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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
        summary="Лучший игрок",
        description="Возвращает игрока с наибольшим общим выигрышем в TON",
        responses={
            200: OpenApiResponse(
                response=TopPlayerSerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=TOP_PLAYER_EXAMPLE
                    )
                ],
            ),
            404: OpenApiResponse(description="Нет игроков с победами"),
        },
        tags=["Games"],
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
    
    @extend_schema(
        summary="История PVP игр",
        description="Возвращает список всех завершённых PVP игр с данными победителей и выигрышей",
        responses={
            200: OpenApiResponse(
                response=PublicPvpGameSerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=PVP_GAME_HISTORY_EXAMPLE
                    )
                ],
            ),
        },
        tags=["Games"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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
    
    @extend_schema(
        summary="Детали PVP-игры",
        description="Возвращает детальную информацию о PVP игре по ID (только завершённые игры)",
        responses={
            200: OpenApiResponse(
                response=PvpGameDetailSerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=PVP_GAME_DETAIL_EXAMPLE
                    )
                ],
            ),
            404: OpenApiResponse(description="Игра не найдена"),
        },
        tags=["Games"],
    )

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
        summary="Игра в спин",
        description="Запускает игру в спин с указанными ставками в Stars и TON",
        request=SpinPlayRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SpinPlayResponseSerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=SPIN_PLAY_RESPONSE_EXAMPLE
                    )
                ],
            ),
            400: OpenApiResponse(description="Ошибка валидации"),
        },
        tags=["Games"],
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
        summary="Сектора колеса спина",
        description="Возвращает все сектора колеса спина с подарками и вероятностями",
        responses={
            200: OpenApiResponse(
                response=SpinWheelSectorSerializer(many=True),
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=SPIN_WHEEL_EXAMPLE
                    )
                ],
            ),
        },
        tags=["Games"],
    )
    def get(self, request):
        # Берём все сектора, сортируя по индексу
        sectors = SpinWheelSector.objects.select_related("gift").all().order_by("index")
        serializer = SpinWheelSectorSerializer(sectors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpinGameHistoryView(ListAPIView):
    serializer_class = SpinGameHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="История игр в спин",
        description="Возвращает историю всех игр в спин для текущего пользователя",
        responses={
            200: OpenApiResponse(
                response=SpinGameHistorySerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=SPIN_GAME_HISTORY_EXAMPLE
                    )
                ],
            ),
        },
        tags=["Games"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            SpinGame.objects
            .select_related("gift_won")
            .order_by("-played_at")
        )

class LastPvpWinnerView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Последний победитель PVP игры",
        description="Возвращает информацию о последнем победителе PVP игры",
        responses={
            200: OpenApiResponse(
                response=LastWinnerSerializer,
                description="Успешный ответ",
                        examples=[
            OpenApiExample(
                name="Пример ответа",
                value=LAST_WINNER_EXAMPLE
            )
        ],
            ),
            404: OpenApiResponse(description="Нет завершённых игр"),
        },
        tags=["Games"],
    )
    def get(self, request):
        last_game, winner_gp = get_last_pvp_winner()

        if not last_game or not winner_gp:
            return Response({"detail": "Нет завершённых игр"}, status=404)

        data = LastWinnerSerializer(winner_gp).data
        data["game_id"] = last_game.id
        return Response(data)


class OnlinePlayersCountView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Количество онлайн игроков",
        description="Возвращает количество уникальных игроков, которые сейчас играют в PVP рулетку (в активных играх со статусом waiting или running)",
        responses={
            200: OpenApiResponse(
                response=OnlinePlayersCountSerializer,
                description="Успешный ответ",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"online_count": 5}
                    )
                ],
            ),
        },
        tags=["Games"],
    )
    def get(self, request):
        online_count = GameService.get_online_players_count()
        serializer = OnlinePlayersCountSerializer({"online_count": online_count})
        return Response(serializer.data, status=status.HTTP_200_OK)