import os
import requests
from PIL import Image
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)


class AvatarService:
    @staticmethod
    def get_default_avatar_url() -> str:
        """Возвращает URL аватарки по умолчанию"""
        return getattr(settings, 'DEFAULT_AVATAR_URL', "https://teststudiaorbita.ru/media/avatars/diamond.png")

    @staticmethod
    def download_and_save_avatar(telegram_user_id: int, bot_token: str) -> str | None:
        """
        Скачивает аватарку пользователя из Telegram и сохраняет локально или на S3.
        Возвращает URL сохраненного файла или None при ошибке.
        """
        if not bot_token:
            logger.error("BOT_TOKEN не настроен в settings.py")
            return None
            
        try:
            # Получаем информацию о фото профиля
            photos_response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos",
                params={"user_id": telegram_user_id, "limit": 1},
                timeout=10
            ).json()

            if not photos_response.get("ok"):
                logger.warning(f"Telegram API вернул ошибку для пользователя {telegram_user_id}: {photos_response.get('description', 'Unknown error')}")
                return None
            
            result = photos_response.get("result", {})
            photos = result.get("photos", [])
            if not photos:
                logger.info(f"Нет фото профиля для пользователя {telegram_user_id}")
                return None

            # Получаем file_id последнего фото (самое большое разрешение)
            file_id = photos[0][-1]["file_id"]
            
            # Получаем информацию о файле
            file_response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": file_id},
                timeout=10
            ).json()

            if not file_response.get("ok"):
                logger.error(f"Ошибка получения файла: {file_response}")
                return None

            file_path = file_response["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

            # Скачиваем файл
            image_response = requests.get(file_url, timeout=30)
            if image_response.status_code != 200:
                logger.error(f"Ошибка скачивания файла: {image_response.status_code}")
                return None

            # Обрабатываем изображение
            image = Image.open(BytesIO(image_response.content))
            
            # Конвертируем в PNG если нужно
            if image.format != 'PNG':
                # Создаем новое изображение в режиме RGBA для поддержки прозрачности
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Если изображение уже имеет альфа-канал, конвертируем в RGBA
                    png_image = image.convert('RGBA')
                else:
                    # Если нет альфа-канала, конвертируем в RGB
                    png_image = image.convert('RGB')
            else:
                png_image = image

            # Оптимизируем размер изображения (максимум 512x512)
            max_size = (512, 512)
            if png_image.size[0] > max_size[0] or png_image.size[1] > max_size[1]:
                png_image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Генерируем уникальное имя файла
            filename = f"avatars/user_{telegram_user_id}_{uuid.uuid4().hex[:8]}.png"
            
            # Убеждаемся, что папка avatars существует
            avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(avatars_dir, exist_ok=True)
            
            # Сохраняем в BytesIO с оптимизацией
            output = BytesIO()
            png_image.save(output, format='PNG', optimize=True, quality=85)
            output.seek(0)

            # Сохраняем файл
            saved_path = default_storage.save(filename, ContentFile(output.getvalue()))
            logger.info(f"Аватарка сохранена: {saved_path}")
            
            # Возвращаем полный URL
            site_url = getattr(settings, 'SITE_URL', 'https://teststudiaorbita.ru')
            # Убираем trailing slash если есть
            site_url = site_url.rstrip('/')
            
            # Формируем путь к медиа файлу
            # saved_path обычно возвращает путь относительно MEDIA_ROOT (например, "avatars/user_123_abc.png")
            # или может вернуть полный путь если используется S3
            if saved_path.startswith('http://') or saved_path.startswith('https://'):
                # Если storage вернул полный URL (S3), используем его
                return saved_path
            
            # Нормализуем путь: убираем начальные слеши
            normalized_path = saved_path.lstrip('/')
            
            # Если путь уже содержит media/, используем как есть, иначе добавляем
            if normalized_path.startswith('media/'):
                media_path = normalized_path
            else:
                media_path = f"media/{normalized_path}"
            
            # Формируем полный URL без двойных слешей
            full_url = f"{site_url}/{media_path}"
            return full_url

        except Exception as e:
            logger.error(f"Ошибка при загрузке аватарки для пользователя {telegram_user_id}: {e}")
            return None

    @staticmethod
    def delete_old_avatar(user_id: int) -> bool:
        """
        Удаляет старую аватарку пользователя.
        В продакшене с S3 лучше использовать lifecycle policies.
        """
        try:
            # Для локального хранения можно реализовать поиск по паттерну
            # Для S3 лучше использовать lifecycle policies или CloudFront invalidation
            logger.info(f"Попытка удаления старой аватарки для пользователя {user_id}")
            
            # В простом случае просто возвращаем True
            # В продакшене здесь должна быть логика поиска и удаления старых файлов
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении старой аватарки для пользователя {user_id}: {e}")
            return False

    @staticmethod
    def get_avatar_url(file_path: str) -> str:
        """
        Возвращает полный URL для аватарки.
        Поддерживает как локальное хранение, так и S3.
        """
        if hasattr(settings, 'MEDIA_URL'):
            return f"{settings.MEDIA_URL}{file_path}"
        else:
            return f"/media/{file_path}"
