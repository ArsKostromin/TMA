import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import games.routing  # твой роутер для WebSocket

# Указываем Django, какой settings использовать
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django должен быть инициализирован до импортов моделей
django.setup()

# HTTP-приложение (обычный Django)
django_asgi_app = get_asgi_application()

# ASGI-приложение с поддержкой HTTP и WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            games.routing.websocket_urlpatterns
        )
    ),
})