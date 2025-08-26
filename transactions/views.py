from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .ton_service import TONService
from .models import TONWallet, TONTransaction, Transaction
from .serializers import (
    TONWalletSerializer, 
    TONTransactionSerializer, 
    DepositAddressSerializer
)

User = get_user_model()
ton_service = TONService()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_deposit_address(request):
    """Создает или получает адрес для пополнения баланса"""
    try:
        user = request.user
        wallet = ton_service.create_wallet_for_user(user)
        
        serializer = TONWalletSerializer(wallet)
        return Response({
            'success': True,
            'wallet': serializer.data,
            'message': 'Адрес для пополнения создан'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deposit_address(request):
    """Получает адрес для пополнения пользователя"""
    try:
        user = request.user
        address = ton_service.get_deposit_address(user)
        
        return Response({
            'success': True,
            'address': address,
            'message': 'Адрес для пополнения получен'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """Получает баланс TON кошелька пользователя"""
    try:
        user = request.user
        
        if not hasattr(user, 'ton_wallet'):
            return Response({
                'success': False,
                'error': 'Кошелек не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        wallet = user.ton_wallet
        ton_balance = ton_service.get_wallet_balance(wallet.address)
        usdt_balance = ton_service.check_usdt_balance(wallet.address)
        
        return Response({
            'success': True,
            'balances': {
                'TON': float(ton_balance),
                'USDT': float(usdt_balance)
            },
            'wallet_address': wallet.address
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_history(request):
    """Получает историю TON транзакций пользователя"""
    try:
        user = request.user
        transactions = TONTransaction.objects.filter(user=user).order_by('-created_at')
        
        serializer = TONTransactionSerializer(transactions, many=True)
        
        return Response({
            'success': True,
            'transactions': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_status(request, tx_hash):
    """Получает статус конкретной транзакции"""
    try:
        user = request.user
        
        # Проверяем, что транзакция принадлежит пользователю
        try:
            transaction = TONTransaction.objects.get(tx_hash=tx_hash, user=user)
        except TONTransaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Транзакция не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Получаем актуальный статус из блокчейна
        blockchain_status = ton_service.get_transaction_status(tx_hash)
        
        serializer = TONTransactionSerializer(transaction)
        
        return Response({
            'success': True,
            'transaction': serializer.data,
            'blockchain_status': blockchain_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_pending_transactions(request):
    """Проверяет и обрабатывает ожидающие транзакции"""
    try:
        # Запускаем проверку транзакций
        ton_service.check_pending_transactions()
        
        return Response({
            'success': True,
            'message': 'Проверка транзакций завершена'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deposit_info(request):
    """Получает полную информацию для пополнения"""
    try:
        user = request.user
        wallet = ton_service.create_wallet_for_user(user)
        
        # Получаем текущие балансы
        ton_balance = ton_service.get_wallet_balance(wallet.address)
        usdt_balance = ton_service.check_usdt_balance(wallet.address)
        
        # Получаем последние транзакции
        recent_transactions = TONTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        serializer = TONTransactionSerializer(recent_transactions, many=True)
        
        return Response({
            'success': True,
            'wallet_address': wallet.address,
            'current_balances': {
                'TON': float(ton_balance),
                'USDT': float(usdt_balance)
            },
            'recent_transactions': serializer.data,
            'supported_tokens': ['TON', 'USDT-TON'],
            'min_deposit': {
                'TON': 0.1,
                'USDT': 1.0
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
