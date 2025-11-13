# games/routing.py
from django.urls import re_path
from games import consumers as pvp_consumers

websocket_urlpatterns = [
    re_path(r"ws/pvp/$", pvp_consumers.PvpGameConsumer.as_asgi()),
]
