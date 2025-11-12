# games/routing.py
from django.urls import re_path
from spin import consumers as spin_consumers
from games import consumers as pvp_consumers

websocket_urlpatterns = [
    re_path(r"ws/spin/$", spin_consumers.SpinGameConsumer.as_asgi()),
    re_path(r"ws/pvp/$", pvp_consumers.PvpGameConsumer.as_asgi()),
]
