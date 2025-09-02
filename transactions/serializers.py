from rest_framework import serializers
from .models import TONWallet, TONTransaction, Transaction


class TONWalletSerializer(serializers.ModelSerializer):
    """Сериализатор для TON кошелька"""
    
    class Meta:
        model = TONWallet
        fields = [
            'id', 'address', 'subwallet_id', 'created_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at']


class TONTransactionSerializer(serializers.ModelSerializer):
    """Сериализатор для TON транзакций"""
    
    class Meta:
        model = TONTransaction
        fields = [
            'id', 'tx_hash', 'amount', 'token', 'status', 
            'sender_address', 'block_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Сериализатор для транзакций приложения"""
    ton_transaction = TONTransactionSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'tx_type', 'amount', 'currency', 'description',
            'created_at', 'ton_transaction'
        ]
        read_only_fields = ['id', 'created_at']


class DepositAddressSerializer(serializers.Serializer):
    """Сериализатор для запроса адреса пополнения"""
    token = serializers.ChoiceField(
        choices=[('TON', 'TON'), ('USDT', 'USDT-TON')],
        default='TON'
    )


class WalletBalanceSerializer(serializers.Serializer):
    """Сериализатор для баланса кошелька"""
    TON = serializers.DecimalField(max_digits=18, decimal_places=9)
    USDT = serializers.DecimalField(max_digits=18, decimal_places=6)


class DepositInfoSerializer(serializers.Serializer):
    """Сериализатор для информации о пополнении"""
    wallet_address = serializers.CharField()
    current_balances = WalletBalanceSerializer()
    recent_transactions = TONTransactionSerializer(many=True)
    supported_tokens = serializers.ListField(
        child=serializers.CharField()
    )
    min_deposit = serializers.DictField(
        child=serializers.DecimalField(max_digits=10, decimal_places=2)
    )


# ===== Swagger-friendly wrapper serializers for responses =====

class SuccessSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)


class WalletAddressCreateResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    wallet = TONWalletSerializer()
    message = serializers.CharField()


class AddressResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    address = serializers.CharField()


class BalanceResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    balances = WalletBalanceSerializer()
    wallet_address = serializers.CharField()


class TransactionsListResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    transactions = TONTransactionSerializer(many=True)