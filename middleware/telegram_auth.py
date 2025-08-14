from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from user.services.auth import AuthService

User = get_user_model()

class TelegramAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            request.user = None
            return

        token = auth_header.split(" ")[1]
        try:
            payload = AuthService.decode_token(token)
            if payload.get("type") != "access":
                request.user = None
                return
            user = User.objects.filter(id=payload["user_id"]).first()
            request.user = user
        except Exception:
            request.user = None
