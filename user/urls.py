from django.urls import path
from .views import TelegramAuthView, RefreshTokenView, LogoutView

urlpatterns = [
    path("auth/telegram/", TelegramAuthView.as_view()),
    path("auth/refresh/", RefreshTokenView.as_view()),
    # path("auth/logout/", LogoutView.as_view()),
]
