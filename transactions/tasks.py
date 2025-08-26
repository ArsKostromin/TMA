from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .ton_service import TONService
from .models import TONWallet, TONTransaction


@shared_task
def check_ton_transactions():
    """Периодическая задача для проверки TON транзакций"""
    try:
        ton_service = TONService()
        ton_service.check_pending_transactions()
        
        print(f"[{timezone.now()}] Проверка TON транзакций завершена")
        return True
        
    except Exception as e:
        print(f"[{timezone.now()}] Ошибка при проверке TON транзакций: {e}")
        return False


@shared_task
def cleanup_old_transactions():
    """Очистка старых транзакций (старше 30 дней)"""
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Удаляем старые неуспешные транзакции
        old_failed_transactions = TONTransaction.objects.filter(
            status='failed',
            created_at__lt=cutoff_date
        )
        deleted_count = old_failed_transactions.count()
        old_failed_transactions.delete()
        
        print(f"[{timezone.now()}] Удалено {deleted_count} старых неуспешных транзакций")
        return True
        
    except Exception as e:
        print(f"[{timezone.now()}] Ошибка при очистке старых транзакций: {e}")
        return False


@shared_task
def update_wallet_balances():
    """Обновление балансов всех активных кошельков"""
    try:
        ton_service = TONService()
        active_wallets = TONWallet.objects.filter(is_active=True)
        
        updated_count = 0
        for wallet in active_wallets:
            try:
                # Получаем актуальные балансы
                ton_balance = ton_service.get_wallet_balance(wallet.address)
                usdt_balance = ton_service.check_usdt_balance(wallet.address)
                
                # Здесь можно добавить логику для обновления баланса пользователя
                # если у модели пользователя есть соответствующие поля
                
                updated_count += 1
                
            except Exception as e:
                print(f"Ошибка обновления баланса для кошелька {wallet.address}: {e}")
                continue
        
        print(f"[{timezone.now()}] Обновлены балансы для {updated_count} кошельков")
        return True
        
    except Exception as e:
        print(f"[{timezone.now()}] Ошибка при обновлении балансов: {e}")
        return False


@shared_task
def process_specific_transaction(tx_hash):
    """Обработка конкретной транзакции по хешу"""
    try:
        ton_service = TONService()
        
        # Получаем данные транзакции из блокчейна
        tx_data = ton_service.get_transaction_status(tx_hash)
        
        if tx_data:
            # Обрабатываем транзакцию
            success = ton_service.process_incoming_transaction(tx_data)
            
            if success:
                print(f"[{timezone.now()}] Транзакция {tx_hash} успешно обработана")
                return True
            else:
                print(f"[{timezone.now()}] Транзакция {tx_hash} не была обработана")
                return False
        else:
            print(f"[{timezone.now()}] Транзакция {tx_hash} не найдена в блокчейне")
            return False
            
    except Exception as e:
        print(f"[{timezone.now()}] Ошибка при обработке транзакции {tx_hash}: {e}")
        return False
