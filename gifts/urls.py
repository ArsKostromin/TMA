# urls.py
from django.urls import path
from .views import UserInventoryView, UserAddsGift, WithdrawalOfNFT, TelegramPaymentWebhook

urlpatterns = [
    path("inventory/", UserInventoryView.as_view(), name="user-inventory"),
    path("adds-gift/", UserAddsGift.as_view(), name="user-adds-gift"),
    path("withdraw/", WithdrawalOfNFT.as_view(), name="withdraw-nft"),
    path("telegram/payment-webhook/", TelegramPaymentWebhook.as_view(), name="telegram-payment-webhook"),
]
