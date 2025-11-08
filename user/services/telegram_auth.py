from django.conf import settings
from django.contrib.auth import get_user_model
from ..utils.telegram_auth import validate_init_data, parse_init_data_no_check
from .auth import AuthService
from .avatar_service import AvatarService

User = get_user_model()


class TelegramAuthService:
    @staticmethod
    def authenticate(init_data: str) -> dict:
        """
        Основная логика аутентификации через Telegram initData
        """
        if settings.DEBUG:
            data = parse_init_data_no_check(init_data)  # dev-режим, без подписи
        else:
            data = validate_init_data(init_data)  # prod — с проверкой HMAC

        tg_user = data.get("user")
        if not tg_user:
            raise ValueError("No user data in initData")

        import logging
        logger = logging.getLogger(__name__)
        
        # Пытаемся загрузить аватарку из Telegram
        avatar_url = AvatarService.download_and_save_avatar(tg_user["id"], settings.BOT_TOKEN)
        if avatar_url:
            logger.info(f"Аватарка успешно загружена для пользователя {tg_user.get('username', tg_user['id'])}: {avatar_url}")
        else:
            logger.warning(f"Не удалось загрузить аватарку для пользователя {tg_user.get('username', tg_user['id'])} (ID: {tg_user['id']})")

        user, created = User.objects.get_or_create(
            telegram_id=tg_user["id"],
            defaults={
                "username": tg_user.get("username", ""),
                "avatar_url": avatar_url
            }
        )

        if not created:
            updated = False
            if user.username != tg_user.get("username", ""):
                user.username = tg_user.get("username", "")
                updated = True
            # Обновляем аватарку только если она была успешно загружена
            if avatar_url and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
                updated = True
            if updated:
                user.save()
                if avatar_url:
                    logger.info(f"Профиль пользователя {user.username} обновлен, новая аватарка: {avatar_url}")

        access = AuthService.create_access_token(user.id)
        refresh = AuthService.create_refresh_token(user.id)

        return {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.get_avatar_url(),
            "access": access,
            "refresh": refresh,
        }
