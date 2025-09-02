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
)

User = get_user_model()
ton_service = TONService()


class WalletViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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


    @decorators.action(detail=False, methods=["get"], url_path="me/address")
    def get_address(self, request):
        """Возвращает адрес кошелька текущего пользователя"""
        try:
            address = ton_service.get_deposit_address(request.user)
            return Response({'success': True, 'address': address}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
