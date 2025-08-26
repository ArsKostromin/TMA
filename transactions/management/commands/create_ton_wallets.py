from django.core.management.base import BaseCommand
from transactions.ton_service import TONService
from transactions.models import TONWallet
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает TON кошельки для пользователей, у которых их нет'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID конкретного пользователя для создания кошелька',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Создать кошельки для всех пользователей',
        )

    def handle(self, *args, **options):
        ton_service = TONService()
        
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                users = [user]
                self.stdout.write(f"Создаем кошелек для пользователя {user.username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Пользователь с ID {options['user_id']} не найден"))
                return
        elif options['all']:
            users = User.objects.all()
            self.stdout.write(f"Создаем кошельки для {users.count()} пользователей")
        else:
            # Создаем кошельки только для пользователей, у которых их нет
            users_without_wallets = []
            for user in User.objects.all():
                if not hasattr(user, 'ton_wallet'):
                    users_without_wallets.append(user)
            
            users = users_without_wallets
            self.stdout.write(f"Создаем кошельки для {len(users)} пользователей без кошельков")

        created_count = 0
        for user in users:
            try:
                if hasattr(user, 'ton_wallet'):
                    self.stdout.write(f"Кошелек для пользователя {user.username} уже существует")
                    continue
                
                wallet = ton_service.create_wallet_for_user(user)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Создан кошелек {wallet.address} для пользователя {user.username}")
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка при создании кошелька для пользователя {user.username}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Операция завершена. Создано {created_count} новых кошельков")
        )
