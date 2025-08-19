# urls.py
from django.urls import path
from .views import UserInventoryView

urlpatterns = [
    path("inventory/", UserInventoryView.as_view(), name="user-inventory"),
]
