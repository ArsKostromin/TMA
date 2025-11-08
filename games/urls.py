from django.urls import path
from .views import GameHistoryView, TopPlayersAPIView, PvPGameHistoryAPIView, PvpGameDetailView, SpinPlayView, SpinWheelView, SpinGameHistoryView, LastPvpWinnerView, OnlinePlayersCountView

urlpatterns = [
    # История игр текущего пользователя (PVP, Daily и пр.) → только авторизованный
    path("history/", GameHistoryView.as_view(), name="game-history"),

    # Топ игроков по выигрышам в PVP → общедоступно
    path("top/", TopPlayersAPIView.as_view(), name="top-players"),

    # Публичная история последних PVP игр → все могут смотреть, даже гости
    path("pvp-history", PvPGameHistoryAPIView.as_view(), name="pvp-history"),

    # Детальная информация о PVP игре по ID → все могут смотреть
    path("pvp-game/<int:game_id>/", PvpGameDetailView.as_view(), name="pvp-game-detail"),

    # Запуск рекламного Spin (ставка Stars/Ton, результат и приз) → только авторизованный
    path("spin/play/", SpinPlayView.as_view(), name="spin-play"),

    # Получить конфигурацию колеса (сектора с шансами и подарками) → доступно всем
    path("spin/wheel/", SpinWheelView.as_view(), name="spin-wheel"),
    
    #история спин игр
    path("spin/history/", SpinGameHistoryView.as_view(), name="spin-history"),

    #послений победитель
    path("last-winner/", LastPvpWinnerView.as_view(), name="last-winner"),
    
    #количество онлайн игроков
    path("online-count/", OnlinePlayersCountView.as_view(), name="online-count"),
]