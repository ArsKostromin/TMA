from django.urls import path
from .views import GameHistoryView

urlpatterns = [
    path("history", GameHistoryView.as_view(), name="game-history"),
]
