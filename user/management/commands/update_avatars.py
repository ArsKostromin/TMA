from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from user.services.avatar_service import AvatarService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Обновляет аватарки всех пользователей из Telegram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Обновить аватарку только для конкретного пользователя'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно обновить все аватарки'
        )

    def handle(self, *args, **options):
        if not settings.BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('BOT_TOKEN не настроен в settings.py')
            )
            return

        user_id = options.get('user_id')
        force = options.get('force')

        if user_id:
            # Обновляем аватарку для конкретного пользователя
            try:
                user = User.objects.get(telegram_id=user_id)
                self.update_user_avatar(user)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Пользователь с telegram_id {user_id} не найден')
                )
        else:
            # Обновляем аватарки для всех пользователей
            users = User.objects.all()
            total_users = users.count()
            
            self.stdout.write(f'Найдено {total_users} пользователей')
            
            updated_count = 0
            for user in users:
                if self.update_user_avatar(user):
                    updated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Обновлено {updated_count} из {total_users} аватарок'
                )
            )

    def update_user_avatar(self, user):
        """Обновляет аватарку для конкретного пользователя"""
        try:
            self.stdout.write(f'Обновление аватарки для пользователя {user.username} (ID: {user.telegram_id})')
            
            # Скачиваем и сохраняем новую аватарку
            new_avatar_url = AvatarService.download_and_save_avatar(
                user.telegram_id, 
                settings.BOT_TOKEN
            )
            
            if new_avatar_url:
                # Удаляем старую аватарку
                AvatarService.delete_old_avatar(user.telegram_id)
                
                # Обновляем URL в базе данных
                user.avatar_url = new_avatar_url
                user.save(update_fields=['avatar_url'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Аватарка обновлена: {new_avatar_url}'
                    )
                )
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Не удалось загрузить аватарку для пользователя {user.username}'
                    )
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при обновлении аватарки для пользователя {user.username}: {e}'
                )
            )
            return False
