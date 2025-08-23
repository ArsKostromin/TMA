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
    def download_and_save_avatar(telegram_user_id: int, bot_token: str) -> str | None:
        """
        Скачивает аватарку пользователя из Telegram и сохраняет локально или на S3.
        Возвращает URL сохраненного файла или None при ошибке.
        """
        try:
            # Получаем информацию о фото профиля
            photos_response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos",
                params={"user_id": telegram_user_id, "limit": 1},
                timeout=10
            ).json()

            if not photos_response.get("ok") or not photos_response["result"]["photos"]:
                logger.info(f"Нет фото профиля для пользователя {telegram_user_id}")
                return None

            # Получаем file_id последнего фото
            file_id = photos_response["result"]["photos"][0][-1]["file_id"]
            
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
            
            # Сохраняем в BytesIO с оптимизацией
            output = BytesIO()
            png_image.save(output, format='PNG', optimize=True, quality=85)
            output.seek(0)

            # Сохраняем файл
            saved_path = default_storage.save(filename, ContentFile(output.getvalue()))
            
            # Возвращаем URL
            if hasattr(settings, 'MEDIA_URL'):
                return f"{settings.MEDIA_URL}{saved_path}"
            else:
                return f"/media/{saved_path}"

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
