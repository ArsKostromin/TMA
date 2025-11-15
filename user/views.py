from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from django.contrib.auth import get_user_model
from .services.auth import AuthService
from .services.telegram_auth import TelegramAuthService
from django.conf import settings
from .utils.telegram_auth import validate_init_data, get_user_avatar, parse_init_data_no_check
from .serializers import (
    RefreshTokenRequestSerializer,
    RefreshTokenResponseSerializer,
    LogoutResponseSerializer,
    TelegramAuthRequestSerializer,
    TelegramAuthResponseSerializer,
    UserBalanceSerializer,
    CreateStarsInvoiceSerializer,
    CreateStarsInvoiceResponseSerializer,
    TelegramWebhookSerializer
)
from .services.telegram_stars import TelegramStarsService
from rest_framework.permissions import IsAuthenticated


User = get_user_model()

class TelegramAuthView(APIView):
    @extend_schema(
        request=TelegramAuthRequestSerializer,
        responses={200: TelegramAuthResponseSerializer},
        summary="Telegram authentication"
    )
    def post(self, request):
        serializer = TelegramAuthRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        init_data = serializer.validated_data["initData"]

        try:
            result = TelegramAuthService.authenticate(init_data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        response_serializer = TelegramAuthResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    @extend_schema(
        request=RefreshTokenRequestSerializer,
        responses={200: RefreshTokenResponseSerializer},
        summary="Обновление access-токена",
        description="Принимает refresh токен и возвращает новый access токен.",
    )
    def post(self, request):
        serializer = RefreshTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["refresh"]

        try:
            payload = AuthService.decode_token(token)
            if payload.get("type") != "refresh":
                return Response({"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        access = AuthService.create_access_token(payload["user_id"])
        return Response({"access": access}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    @extend_schema(
        responses={200: LogoutResponseSerializer},
        summary="Выход из системы",
        description="Фактически ничего не делает (refresh токен не инвалидируется), просто возвращает сообщение."
    )
    def post(self, request):
        return Response({"message": "Logged out"}, status=status.HTTP_200_OK)


class UserBalanceView(APIView):
    @extend_schema(
        responses={200: UserBalanceSerializer},
        summary="Получение баланса пользователя",
        description="Возвращает текущий баланс TON, Stars и количество подарков в инвентаре для аутентифицированного пользователя."
    )
    def get(self, request):
        user = request.user
        # Подсчитываем количество подарков в инвентаре пользователя
        gift_count = user.gifts.count()
        
        serializer = UserBalanceSerializer({
            'balance_ton': user.balance_ton,
            'balance_stars': user.balance_stars,
            'gift_count': gift_count
        }, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateStarsInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создать Telegram Stars инвойс",
        description=(
            "Создаёт ссылку на оплату через Telegram Stars. "
            "Пользователь определяется по токену авторизации. "
            "На вход принимает сумму в звёздах."
        ),
        request=CreateStarsInvoiceSerializer,
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={"amount_stars": 150},
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Успешный ответ",
                response=CreateStarsInvoiceResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример успешного ответа",
                        value={
                            "invoice_link": "https://t.me/p2p/pay?start=abc123",
                        },
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Ошибка Telegram API",
                examples=[
                    OpenApiExample(
                        name="Ошибка примера",
                        value={
                            "ok": False,
                            "error": "Bad Request: Invalid price amount",
                            "raw": {}
                        }
                    )
                ]
            ),
        },
        tags=["payments"],
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateStarsInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount_stars"]
        user = request.user

        payload = {
            "user_id": user.telegram_id
        }

        invoice = TelegramStarsService.create_invoice(
            amount_stars=amount,
            title="Участие в игре",
            description=f"Ставка пользователя {user.telegram_id}",
            payload=payload,
        )

        if not invoice.get("ok"):
            return Response(
                {
                    "ok": False,
                    "error": invoice.get("error"),
                    "raw": invoice.get("raw"),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "invoice_link": invoice["invoice_link"],
            },
            status=status.HTTP_200_OK
        )


@method_decorator(csrf_exempt, name="dispatch")
class TelegramStarsWebhookView(APIView):
    authentication_classes = []   # Telegram не авторизуется
    permission_classes = []       # Вебхук публичный
    throttle_classes = []         # Не душим его

    def post(self, request, *args, **kwargs):
        serializer = TelegramWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=False)

        data = serializer.validated_data
        logger.info(f"📩 Telegram webhook: {data}")

        message = data.get("message")
        if not message:
            return Response({"ok": True})

        payment = message.get("successful_payment")
        if not payment:
            return Response({"ok": True})

        # извлечение данных 
        try:
            raw_from = message["from_user"]
            telegram_id = raw_from.get("id")
        except Exception:
            telegram_id = None

        if not telegram_id:
            logger.error("❌ Telegram ID отсутствует")
            return Response({"ok": True})

        total_amount = payment["total_amount"]
        payload_raw = payment["invoice_payload"]

        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            payload = {}

        # ищем юзера
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            logger.error(f"Юзер {telegram_id} не найден")
            return Response({"ok": True})

        # пополнение
        user.add_stars(total_amount)
        logger.info(f"✨ Пополнение Stars: user={telegram_id} +{total_amount}")

        return Response({"ok": True}, status=status.HTTP_200_OK)