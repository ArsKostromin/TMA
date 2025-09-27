from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger('games.services.auth')

class AuthService:
    @staticmethod
    async def get_user_from_token(token):
        try:
            import jwt
            from django.conf import settings
            
            logger.info(f"Попытка аутентификации по токену: {token[:20]}...")
            
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("user_id")
            
            if not user_id:
                logger.warning("Токен не содержит user_id")
                return None
                
            logger.info(f"Найден user_id в токене: {user_id}")
            
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)
            
            logger.info(f"Пользователь найден: {user.username} (ID: {user.id})")
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Токен истек")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Невалидный токен: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {str(e)}")
            return None

    @staticmethod
    async def get_authenticated_user(token: str):
        """
        Возвращает авторизованного пользователя по JWT-токену или None.
        """
        try:
            import jwt
            from django.conf import settings

            if not token:
                logger.warning("Пустой токен при попытке аутентификации")
                return None

            logger.info(f"Попытка аутентификации пользователя по токену: {token[:20]}...")

            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get("user_id")
            
            if not user_id:
                logger.warning("Токен не содержит user_id")
                return None

            logger.info(f"Найден user_id в токене: {user_id}")

            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)
            
            logger.info(f"Пользователь найден в БД: {user.username} (ID: {user.id})")

            # если пользователь деактивирован или гость
            if not getattr(user, "is_authenticated", False):
                logger.warning(f"Пользователь {user.username} (ID: {user.id}) не аутентифицирован или деактивирован")
                return None

            logger.info(f"Пользователь {user.username} (ID: {user.id}) успешно аутентифицирован")
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Токен истек при аутентификации")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Невалидный токен при аутентификации: {str(e)}")
            return None
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден в БД")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при аутентификации: {str(e)}")
            return None