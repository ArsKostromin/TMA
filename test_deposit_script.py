#!/usr/bin/env python
"""
Скрипт для создания тестовой транзакции пополнения
Запустите этот скрипт для симуляции пополнения TON кошелька
"""

import os
import sys
import django
from decimal import Decimal

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from transactions.models import TONWallet, TONTransaction, Transaction
from transactions.ton_service import TONService

User = get_user_model()

def create_test_deposit(user_id, amount_ton=1.0, amount_usdt=10.0):
    """Создает тестовую транзакцию пополнения для пользователя"""
    
    try:
        # Получаем пользователя
        user = User.objects.get(id=user_id)
        print(f"Пользователь найден: {user.username}")
        
        # Получаем или создаем кошелек
        ton_service = TONService()
        wallet = ton_service.create_wallet_for_user(user)
        print(f"Кошелек: {wallet.address}")
        
        # Создаем тестовую TON транзакцию
        if amount_ton > 0:
            ton_tx = TONTransaction.objects.create(
                user=user,
                wallet=wallet,
                tx_hash=f"test_ton_{user_id}_{int(time.time())}",
                amount=Decimal(str(amount_ton)),
                token="TON",
                status="confirmed",
                sender_address="test_sender_ton",
                block_time=timezone.now()
            )
            
            # Создаем транзакцию в приложении
            Transaction.objects.create(
                user=user,
                tx_type="deposit",
                amount=Decimal(str(amount_ton)),
                currency="TON",
                description="Тестовое пополнение TON",
                ton_transaction=ton_tx
            )
            print(f"Создана TON транзакция: {amount_ton} TON")
        
        # Создаем тестовую USDT транзакцию
        if amount_usdt > 0:
            usdt_tx = TONTransaction.objects.create(
                user=user,
                wallet=wallet,
                tx_hash=f"test_usdt_{user_id}_{int(time.time())}",
                amount=Decimal(str(amount_usdt)),
                token="USDT",
                status="confirmed",
                sender_address="test_sender_usdt",
                block_time=timezone.now()
            )
            
            # Создаем транзакцию в приложении
            Transaction.objects.create(
                user=user,
                tx_type="deposit",
                amount=Decimal(str(amount_usdt)),
                currency="USDT",
                description="Тестовое пополнение USDT",
                ton_transaction=usdt_tx
            )
            print(f"Создана USDT транзакция: {amount_usdt} USDT")
        
        print("✅ Тестовые транзакции созданы успешно!")
        return True
        
    except User.DoesNotExist:
        print(f"❌ Пользователь с ID {user_id} не найден")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def list_users():
    """Показывает список пользователей"""
    users = User.objects.all()[:10]  # Показываем первых 10
    print("Доступные пользователи:")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, First name: {user.first_name}")
    print()

if __name__ == "__main__":
    import time
    from django.utils import timezone
    
    print("🔧 Скрипт создания тестовых транзакций")
    print("=" * 50)
    
    # Показываем пользователей
    list_users()
    
    # Запрашиваем ID пользователя
    try:
        user_id = int(input("Введите ID пользователя для создания тестовой транзакции: "))
        amount_ton = float(input("Сумма TON для пополнения (0 для пропуска): ") or "0")
        amount_usdt = float(input("Сумма USDT для пополнения (0 для пропуска): ") or "0")
        
        if amount_ton == 0 and amount_usdt == 0:
            print("❌ Необходимо указать хотя бы одну сумму")
            sys.exit(1)
        
        create_test_deposit(user_id, amount_ton, amount_usdt)
        
    except ValueError:
        print("❌ Неверный формат данных")
    except KeyboardInterrupt:
        print("\n👋 Отменено пользователем")
