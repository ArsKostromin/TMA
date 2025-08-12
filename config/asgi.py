import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import games.routing

from middleware.telegram_auth import TelegramAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TelegramAuthMiddlewareStack(
        URLRouter(
            games.routing.websocket_urlpatterns
        )
    ),
})
