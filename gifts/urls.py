# urls.py
from django.urls import path
from .views import UserInventoryView, UserAddsGift, WithdrawGiftView

urlpatterns = [
    path("inventory/", UserInventoryView.as_view(), name="user-inventory"),
    path("adds-gift/", UserAddsGift.as_view(), name="user-adds-gift"),
    path("withdraw/", WithdrawGiftView.as_view(), name="gift-withdraw"),
]
