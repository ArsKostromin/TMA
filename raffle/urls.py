from django.urls import path

from .views import CurrentRaffleView


urlpatterns = [
    path("api/raffle/current", CurrentRaffleView.as_view()),
]


