from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from .models import TONWallet, TONTransaction, Transaction
from .ton_service import TONService

User = get_user_model()


class TONWalletModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_ton_wallet_creation(self):
        """Тест создания TON кошелька"""
        wallet = TONWallet.objects.create(
            user=self.user,
            address='UQ1234567890abcdef',
            subwallet_id=123
        )
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.address, 'UQ1234567890abcdef')
        self.assertEqual(wallet.subwallet_id, 123)
        self.assertTrue(wallet.is_active)
        self.assertIsNotNone(wallet.created_at)

    def test_ton_wallet_str(self):
        """Тест строкового представления кошелька"""
        wallet = TONWallet.objects.create(
            user=self.user,
            address='UQ1234567890abcdef',
            subwallet_id=123
        )
        
        expected_str = f"TON кошелек {self.user.username}: UQ1234567890abcdef"
        self.assertEqual(str(wallet), expected_str)


class TONTransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.wallet = TONWallet.objects.create(
            user=self.user,
            address='UQ1234567890abcdef',
            subwallet_id=123
        )

    def test_ton_transaction_creation(self):
        """Тест создания TON транзакции"""
        transaction = TONTransaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            tx_hash='abc123def456',
            amount=Decimal('10.5'),
            token='TON',
            status='confirmed',
            sender_address='UQsender123'
        )
        
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.tx_hash, 'abc123def456')
        self.assertEqual(transaction.amount, Decimal('10.5'))
        self.assertEqual(transaction.token, 'TON')
        self.assertEqual(transaction.status, 'confirmed')
        self.assertEqual(transaction.sender_address, 'UQsender123')

    def test_ton_transaction_str(self):
        """Тест строкового представления транзакции"""
        transaction = TONTransaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            tx_hash='abc123def456',
            amount=Decimal('10.5'),
            token='TON',
            status='confirmed'
        )
        
        expected_str = "TON транзакция abc123def4... (confirmed)"
        self.assertEqual(str(transaction), expected_str)


class TONServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ton_service = TONService()

    def test_generate_subwallet_address(self):
        """Тест генерации адреса субкошелька"""
        address, subwallet_id = self.ton_service.generate_subwallet_address(self.user.id)
        
        self.assertIsInstance(address, str)
        self.assertIsInstance(subwallet_id, int)
        self.assertTrue(address.startswith('UQ'))
        self.assertGreater(subwallet_id, 0)

    def test_create_wallet_for_user(self):
        """Тест создания кошелька для пользователя"""
        wallet = self.ton_service.create_wallet_for_user(self.user)
        
        self.assertIsInstance(wallet, TONWallet)
        self.assertEqual(wallet.user, self.user)
        self.assertTrue(wallet.is_active)
        self.assertIsNotNone(wallet.address)
        self.assertIsNotNone(wallet.subwallet_id)

    def test_create_wallet_for_user_existing(self):
        """Тест создания кошелька для пользователя, у которого уже есть кошелек"""
        # Создаем первый кошелек
        wallet1 = self.ton_service.create_wallet_for_user(self.user)
        
        # Пытаемся создать второй кошелек
        wallet2 = self.ton_service.create_wallet_for_user(self.user)
        
        # Должен вернуться тот же кошелек
        self.assertEqual(wallet1.id, wallet2.id)
        self.assertEqual(wallet1.address, wallet2.address)


class TONAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_deposit_address(self):
        """Тест API создания адреса для пополнения"""
        url = reverse('transactions:create_deposit_address')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('wallet', response.data)
        self.assertEqual(response.data['wallet']['user'], self.user.id)

    def test_get_deposit_address(self):
        """Тест API получения адреса пополнения"""
        url = reverse('transactions:get_deposit_address')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('address', response.data)

    def test_get_deposit_info(self):
        """Тест API получения полной информации для пополнения"""
        url = reverse('transactions:get_deposit_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('wallet_address', response.data)
        self.assertIn('current_balances', response.data)
        self.assertIn('supported_tokens', response.data)

    def test_get_transaction_history(self):
        """Тест API получения истории транзакций"""
        url = reverse('transactions:get_transaction_history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('transactions', response.data)

    def test_check_pending_transactions(self):
        """Тест API проверки ожидающих транзакций"""
        url = reverse('transactions:check_pending_transactions')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_unauthorized_access(self):
        """Тест доступа без авторизации"""
        self.client.force_authenticate(user=None)
        
        url = reverse('transactions:get_deposit_address')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TransactionIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ton_service = TONService()

    def test_transaction_creation_from_ton_transaction(self):
        """Тест создания транзакции приложения из TON транзакции"""
        # Создаем кошелек
        wallet = self.ton_service.create_wallet_for_user(self.user)
        
        # Создаем TON транзакцию
        ton_tx = TONTransaction.objects.create(
            user=self.user,
            wallet=wallet,
            tx_hash='test_hash_123',
            amount=Decimal('5.0'),
            token='TON',
            status='confirmed',
            sender_address='UQsender123'
        )
        
        # Создаем транзакцию приложения
        app_tx = Transaction.objects.create(
            user=self.user,
            tx_type='deposit',
            amount=Decimal('5.0'),
            currency='TON',
            description='Пополнение через TON кошелек',
            ton_transaction=ton_tx
        )
        
        self.assertEqual(app_tx.user, self.user)
        self.assertEqual(app_tx.tx_type, 'deposit')
        self.assertEqual(app_tx.amount, Decimal('5.0'))
        self.assertEqual(app_tx.currency, 'TON')
        self.assertEqual(app_tx.ton_transaction, ton_tx)
        self.assertTrue(app_tx.is_income)

    def test_transaction_properties(self):
        """Тест свойств транзакции"""
        # Создаем транзакцию пополнения
        deposit_tx = Transaction.objects.create(
            user=self.user,
            tx_type='deposit',
            amount=Decimal('10.0'),
            currency='TON'
        )
        
        # Создаем транзакцию ставки
        bet_tx = Transaction.objects.create(
            user=self.user,
            tx_type='bet',
            amount=Decimal('5.0'),
            currency='TON'
        )
        
        self.assertTrue(deposit_tx.is_income)
        self.assertFalse(deposit_tx.is_outcome)
        self.assertFalse(bet_tx.is_income)
        self.assertTrue(bet_tx.is_outcome)
