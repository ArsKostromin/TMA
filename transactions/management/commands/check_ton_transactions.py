from django.core.management.base import BaseCommand
from transactions.ton_service import TONService
from transactions.models import TONWallet, TONTransaction
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Проверяет TON транзакции для всех активных кошельков'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID конкретного пользователя для проверки',
        )
        parser.add_argument(
            '--wallet-address',
            type=str,
            help='Адрес конкретного кошелька для проверки',
        )

    def handle(self, *args, **options):
        ton_service = TONService()
        
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                wallets = [user.ton_wallet] if hasattr(user, 'ton_wallet') else []
                self.stdout.write(f"Проверяем кошелек пользователя {user.username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Пользователь с ID {options['user_id']} не найден"))
                return
        elif options['wallet_address']:
            try:
                wallet = TONWallet.objects.get(address=options['wallet_address'])
                wallets = [wallet]
                self.stdout.write(f"Проверяем кошелек {wallet.address}")
            except TONWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Кошелек {options['wallet_address']} не найден"))
                return
        else:
            wallets = TONWallet.objects.filter(is_active=True)
            self.stdout.write(f"Проверяем {wallets.count()} активных кошельков")

        processed_count = 0
        for wallet in wallets:
            try:
                self.stdout.write(f"Проверяем кошелек {wallet.address} (пользователь: {wallet.user.username})")
                
                # Получаем транзакции
                transactions = ton_service.get_wallet_transactions(wallet.address, limit=10)
                
                for tx in transactions:
                    if tx.get("in_msg", {}).get("source") != wallet.address:  # Входящая транзакция
                        success = ton_service.process_incoming_transaction(tx)
                        if success:
                            processed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"Обработана транзакция {tx.get('hash', 'unknown')}")
                            )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка при проверке кошелька {wallet.address}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Проверка завершена. Обработано {processed_count} новых транзакций")
        )
