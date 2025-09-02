from django.shortcuts import render
from rest_framework import status, viewsets, mixins, decorators
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .ton_service import TONService
from .models import TONWallet, TONTransaction, Transaction
from .serializers import (
    TONWalletSerializer,
    TONTransactionSerializer,
    WalletAddressCreateResponseSerializer,
    AddressResponseSerializer,
    BalanceResponseSerializer,
    TransactionsListResponseSerializer,
    DepositAddressSerializer,
)
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter

User = get_user_model()
ton_service = TONService()


class WalletViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Создает или возвращает адрес кошелька текущего пользователя",
        request=DepositAddressSerializer,
        responses={201: WalletAddressCreateResponseSerializer},
        parameters=[],
        examples=[
            OpenApiExample(
                name="Успешное создание/получение адреса",
                value={
                    "success": True,
                    "wallet": {
                        "id": 12,
                        "address": "UQ000006_6_1756799783",
                        "subwallet_id": 6,
                        "created_at": "2024-01-01T12:00:00Z",
                        "is_active": True
                    },
                    "message": "Адрес для пополнения создан или уже существует"
                },
            )
        ],
        tags=["Wallets"],
    )
    @decorators.action(detail=False, methods=["post"], url_path="me/address")
    def create_or_get_address(self, request):
        """Создает или возвращает адрес кошелька текущего пользователя"""
        try:
            wallet = ton_service.create_wallet_for_user(request.user)
            return Response({
                'success': True,
                'wallet': TONWalletSerializer(wallet).data,
                'message': 'Адрес для пополнения создан или уже существует'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(
        description="Возвращает адрес кошелька текущего пользователя",
        responses={200: AddressResponseSerializer},
        parameters=[],
        examples=[
            OpenApiExample(
                name="Успешный ответ",
                value={"success": True, "address": "UQ000006_6_1756799783"},
            )
        ],
        tags=["Wallets"],
    )
    @decorators.action(detail=False, methods=["get"], url_path="me/address")
    def get_address(self, request):
        """Возвращает адрес кошелька текущего пользователя"""
        try:
            address = ton_service.get_deposit_address(request.user)
            return Response({'success': True, 'address': address}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(
        description="Возвращает балансы TON/USDT для кошелька текущего пользователя",
        responses={200: BalanceResponseSerializer},
        parameters=[],
        examples=[
            OpenApiExample(
                name="Успешный ответ",
                value={
                    "success": True,
                    "balances": {"TON": 1.23, "USDT": 0},
                    "wallet_address": "UQ000006_6_1756799783"
                },
            )
        ],
        tags=["Wallets"],
    )
    @decorators.action(detail=False, methods=["get"], url_path="me/balance")
    def balance(self, request):
        """Возвращает балансы TON/USDT для кошелька текущего пользователя"""
        try:
            if not hasattr(request.user, 'ton_wallet'):
                return Response({'success': False, 'error': 'Кошелек не найден'}, status=status.HTTP_404_NOT_FOUND)
            wallet = request.user.ton_wallet
            ton_balance = ton_service.get_wallet_balance(wallet.address)
            usdt_balance = ton_service.check_usdt_balance(wallet.address)
            return Response({
                'success': True,
                'balances': {'TON': float(ton_balance), 'USDT': float(usdt_balance)},
                'wallet_address': wallet.address
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @extend_schema(
        description="История TON-транзакций текущего пользователя",
        responses={200: TransactionsListResponseSerializer},
        parameters=[
            OpenApiParameter(name="limit", type=int, location=OpenApiParameter.QUERY, required=False, description="Количество элементов на странице (по умолчанию settings.PAGE_SIZE)"),
            OpenApiParameter(name="offset", type=int, location=OpenApiParameter.QUERY, required=False, description="Смещение для пагинации"),
        ],
        examples=[
            OpenApiExample(
                name="Пример ответа",
                value={
                    "success": True,
                    "transactions": [
                        {
                            "id": 1,
                            "tx_hash": "test_ton_6_1756799783",
                            "amount": "1.000000000",
                            "token": "TON",
                            "status": "confirmed",
                            "sender_address": "test_sender_ton",
                            "block_time": "2024-01-01T12:00:00Z",
                            "created_at": "2024-01-01T12:00:00Z",
                            "updated_at": "2024-01-01T12:00:00Z"
                        }
                    ]
                },
            )
        ],
        tags=["Wallets"],
    )
    @decorators.action(detail=False, methods=["get"], url_path="me/transactions")
    def transactions(self, request):
        """История TON-транзакций текущего пользователя"""
        try:
            transactions = TONTransaction.objects.filter(user=request.user).order_by('-created_at')
            return Response({
                'success': True,
                'transactions': TONTransactionSerializer(transactions, many=True).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
