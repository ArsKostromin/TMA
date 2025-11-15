from django.urls import path
from .views import TelegramAuthView, RefreshTokenView, LogoutView, UserBalanceView, CreateStarsInvoiceView, TelegramStarsWebhookView

urlpatterns = [
    path("auth/telegram/", TelegramAuthView.as_view()),
    path("auth/refresh/", RefreshTokenView.as_view()),
    # path("auth/logout/", LogoutView.as_view()),
    path("balance/", UserBalanceView.as_view()),
    path("create-stars-invoice/", CreateStarsInvoiceView.as_view()),
    path("telegram/stars/webhook/", TelegramStarsWebhookView.as_view(), name="telegram-stars-webhook"),

]
