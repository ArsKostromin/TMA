from django.urls import path
from .views import GameHistoryView, TopPlayersAPIView, PvPGameHistoryAPIView

urlpatterns = [
    path("history", GameHistoryView.as_view(), name="game-history"),
    path("top", TopPlayersAPIView.as_view(), name="top-players"),
    path("pvp-history", PvPGameHistoryAPIView.as_view(), name="pvp-history"),
]