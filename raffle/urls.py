from django.urls import path

from .views import CurrentRaffleView, JoinRaffleView


urlpatterns = [
    path("api/raffle/current", CurrentRaffleView.as_view()),
    path("api/raffle/join", JoinRaffleView.as_view()),
]


