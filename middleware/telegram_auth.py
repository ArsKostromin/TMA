from urllib.parse import parse_qs
from asgiref.sync import sync_to_async
from django.conf import settings  # правильный импорт настроек
import jwt
import logging

logger = logging.getLogger(__name__)

class TelegramAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        logger.info(f"WS Connection attempt with query_string: {query_string}")
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        if token:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
                user_id = payload.get("user_id")

                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = await sync_to_async(User.objects.get)(id=user_id)
                scope['user'] = user
            except jwt.exceptions.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {e}")
                from django.contrib.auth.models import AnonymousUser
                scope['user'] = AnonymousUser()
            except User.DoesNotExist:
                logger.warning(f"User with id={user_id} not found")
                from django.contrib.auth.models import AnonymousUser
                scope['user'] = AnonymousUser()
        else:
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)


def TelegramAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack
    return TelegramAuthMiddleware(AuthMiddlewareStack(inner))
