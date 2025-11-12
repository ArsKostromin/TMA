import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Указываем Django, какой settings использовать
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django должен быть инициализирован до импортов моделей
django.setup()

# Теперь можно безопасно импортировать роутеры, которые используют модели
from games.routing import websocket_urlpatterns as games_ws
from spin.routing import websocket_urlpatterns as spin_ws

# Объединяем все WebSocket роуты в один список
all_websocket_urlpatterns = games_ws + spin_ws

# HTTP-приложение (обычный Django)
django_asgi_app = get_asgi_application()

# ASGI-приложение с поддержкой HTTP и WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_websocket_urlpatterns
        )
    ),
})
