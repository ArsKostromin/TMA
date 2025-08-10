from django.urls import path
from .views import TelegramAuthView

urlpatterns = [
    path("auth/telegram/", TelegramAuthView.as_view(), name="telegram_auth"),
]
