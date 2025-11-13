from django.urls import path
from .views import SpinPlayView, SpinWheelView, SpinWheelView, SpinGameHistoryView, TelegramStarsWebhookView

urlpatterns = [
    # Запуск рекламного Spin (ставка Stars/Ton, результат и приз) → только авторизованный
    path("spin/play/", SpinPlayView.as_view(), name="spin-play"),

    # Получить конфигурацию колеса (сектора с шансами и подарками) → доступно всем
    path("spin/wheel/", SpinWheelView.as_view(), name="spin-wheel"),
    
    # история спин игр
    path("spin/history/", SpinGameHistoryView.as_view(), name="spin-history"),

    path("telegram/webhook/", TelegramStarsWebhookView.as_view(), name="telegram-stars-webhook"),

]