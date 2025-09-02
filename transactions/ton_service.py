import requests
import time
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import TONWallet, TONTransaction, Transaction


class TONService:
    """Сервис для работы с TON кошельками и транзакциями"""
    
    def __init__(self):
        # Берем из settings, чтобы легко переключать окружения
        self.master_wallet_address = getattr(settings, "TON_MASTER_WALLET", "")
        self.ton_api_base_url = getattr(settings, "TON_API_BASE_URL", "https://toncenter.com/api/v2")
        self.usdt_contract_address = getattr(settings, "USDT_CONTRACT_ADDRESS", "")  # USDT-TON контракт
        self.ton_api_key = getattr(settings, "TON_API_KEY", None)
        
    def generate_subwallet_address(self, user_id):
        """Генерирует уникальный адрес субкошелька для пользователя"""
        # Используем user_id как основу для генерации subwallet_id
        subwallet_id = user_id % 1000000  # Ограничиваем размер
        
        # В реальной реализации здесь должна быть интеграция с TON SDK
        # для генерации настоящего субкошелька
        # Пока используем упрощенную логику
        address = f"UQ{subwallet_id:06d}_{user_id}_{int(time.time())}"
        
        return address, subwallet_id
    
    def create_wallet_for_user(self, user):
        """Создает TON кошелек для пользователя"""
        if hasattr(user, 'ton_wallet'):
            return user.ton_wallet
            
        address, subwallet_id = self.generate_subwallet_address(user.id)
        
        wallet = TONWallet.objects.create(
            user=user,
            address=address,
            subwallet_id=subwallet_id
        )
        
        return wallet
    
    def get_wallet_balance(self, wallet_address):
        """Получает баланс кошелька через TON API"""
        try:
            params = {"address": wallet_address}
            if self.ton_api_key:
                params["api_key"] = self.ton_api_key
            response = requests.get(
                f"{self.ton_api_base_url}/getAddressBalance",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                balance = Decimal(data["result"]) / Decimal("1000000000")  # Конвертируем из нанотонов
                return balance
            return Decimal("0")
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return Decimal("0")
    
    def get_wallet_transactions(self, wallet_address, limit=100):
        """Получает транзакции кошелька через TON API"""
        try:
            params = {"address": wallet_address, "limit": limit}
            if self.ton_api_key:
                params["api_key"] = self.ton_api_key
            response = requests.get(
                f"{self.ton_api_base_url}/getTransactions",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                return data["result"]
            return []
        except Exception as e:
            print(f"Ошибка получения транзакций: {e}")
            return []
    
    def check_usdt_balance(self, wallet_address):
        """Проверяет баланс USDT-TON через Jetton API"""
        try:
            params = {"account": wallet_address, "jetton_master": self.usdt_contract_address}
            if self.ton_api_key:
                params["api_key"] = self.ton_api_key
            response = requests.get(
                f"{self.ton_api_base_url}/getJettonWalletData",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                balance = Decimal(data["result"]["balance"]) / Decimal("1000000")  # USDT имеет 6 знаков после запятой
                return balance
            return Decimal("0")
        except Exception as e:
            print(f"Ошибка получения USDT баланса: {e}")
            return Decimal("0")
    
    def process_incoming_transaction(self, tx_data):
        """Обрабатывает входящую транзакцию"""
        try:
            tx_hash = tx_data.get("hash")
            if not tx_hash:
                return False
                
            # Проверяем, не обрабатывали ли мы уже эту транзакцию
            if TONTransaction.objects.filter(tx_hash=tx_hash).exists():
                return False
            
            # Получаем данные транзакции
            amount = Decimal(tx_data.get("amount", 0)) / Decimal("1000000000")
            sender = tx_data.get("sender", "")
            recipient = tx_data.get("recipient", "")
            
            # Ищем кошелек получателя
            try:
                wallet = TONWallet.objects.get(address=recipient)
            except TONWallet.DoesNotExist:
                return False
            
            # Определяем тип токена (TON или USDT)
            token = "TON"
            if tx_data.get("jetton_master") == self.usdt_contract_address:
                token = "USDT"
                amount = Decimal(tx_data.get("amount", 0)) / Decimal("1000000")
            
            # Создаем запись о TON транзакции
            ton_tx = TONTransaction.objects.create(
                user=wallet.user,
                wallet=wallet,
                tx_hash=tx_hash,
                amount=amount,
                token=token,
                status="confirmed",
                sender_address=sender,
                block_time=timezone.now()
            )
            
            # Создаем запись о транзакции в приложении
            currency = "TON" if token == "TON" else "USDT"
            Transaction.objects.create(
                user=wallet.user,
                tx_type="deposit",
                amount=amount,
                currency=currency,
                description=f"Пополнение через TON кошелек",
                ton_transaction=ton_tx
            )
            
            # Обновляем TON баланс пользователя, если поле присутствует
            if hasattr(wallet.user, 'balance_ton'):
                wallet.user.balance_ton += amount
                wallet.user.save(update_fields=["balance_ton"]) 
            
            return True
            
        except Exception as e:
            print(f"Ошибка обработки транзакции: {e}")
            return False
    
    def check_pending_transactions(self):
        """Проверяет все активные кошельки на наличие новых транзакций"""
        active_wallets = TONWallet.objects.filter(is_active=True)
        
        for wallet in active_wallets:
            transactions = self.get_wallet_transactions(wallet.address, limit=10)
            
            for tx in transactions:
                if tx.get("in_msg", {}).get("source") != wallet.address:  # Входящая транзакция
                    self.process_incoming_transaction(tx)
    
    def get_deposit_address(self, user):
        """Получает или создает адрес для пополнения для пользователя"""
        wallet = self.create_wallet_for_user(user)
        return wallet.address
    
    def get_transaction_status(self, tx_hash):
        """Получает статус транзакции по хешу"""
        try:
            params = {"hash": tx_hash}
            if self.ton_api_key:
                params["api_key"] = self.ton_api_key
            response = requests.get(
                f"{self.ton_api_base_url}/getTransaction",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                return data["result"]
            return None
        except Exception as e:
            print(f"Ошибка получения статуса транзакции: {e}")
            return None
