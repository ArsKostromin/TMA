from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .services.auth import AuthService

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = AuthService.decode_token(token)
        except Exception as e:
            raise AuthenticationFailed(str(e))

        if payload.get("type") != "access":
            raise AuthenticationFailed("Invalid token type")

        User = get_user_model()
        user = User.objects.filter(id=payload["user_id"]).first()
        if not user:
            raise AuthenticationFailed("User not found")

        return (user, None)
