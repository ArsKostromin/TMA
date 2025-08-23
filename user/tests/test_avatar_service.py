from django.test import TestCase, override_settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from unittest.mock import patch, MagicMock
from PIL import Image
from io import BytesIO
import tempfile
import os

from user.services.avatar_service import AvatarService


class AvatarServiceTest(TestCase):
    def setUp(self):
        # Создаем временное изображение для тестов
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.image_buffer = BytesIO()
        self.test_image.save(self.image_buffer, format='PNG')
        self.image_buffer.seek(0)

    def tearDown(self):
        # Очищаем временные файлы
        if hasattr(self, 'temp_dir'):
            import shutil
            shutil.rmtree(self.temp_dir)

    @patch('user.services.avatar_service.requests.get')
    def test_download_and_save_avatar_success(self, mock_get):
        """Тест успешной загрузки и сохранения аватарки"""
        # Мокаем ответы API Telegram
        mock_photos_response = MagicMock()
        mock_photos_response.json.return_value = {
            "ok": True,
            "result": {
                "photos": [[{"file_id": "test_file_id"}]]
            }
        }

        mock_file_response = MagicMock()
        mock_file_response.json.return_value = {
            "ok": True,
            "result": {
                "file_path": "photos/test_photo.jpg"
            }
        }

        mock_image_response = MagicMock()
        mock_image_response.status_code = 200
        mock_image_response.content = self.image_buffer.getvalue()

        # Настраиваем mock для последовательных вызовов
        mock_get.side_effect = [
            mock_photos_response,
            mock_file_response,
            mock_image_response
        ]

        # Вызываем тестируемый метод
        result = AvatarService.download_and_save_avatar(12345, "test_bot_token")

        # Проверяем результат
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('/media/avatars/'))
        self.assertTrue(result.endswith('.png'))

        # Проверяем, что файл действительно сохранен
        filename = result.replace('/media/', '')
        self.assertTrue(default_storage.exists(filename))

    @patch('user.services.avatar_service.requests.get')
    def test_download_and_save_avatar_no_photos(self, mock_get):
        """Тест случая, когда у пользователя нет фото профиля"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "result": {
                "photos": []
            }
        }
        mock_get.return_value = mock_response

        result = AvatarService.download_and_save_avatar(12345, "test_bot_token")
        self.assertIsNone(result)

    @patch('user.services.avatar_service.requests.get')
    def test_download_and_save_avatar_api_error(self, mock_get):
        """Тест обработки ошибок API Telegram"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": False,
            "description": "API Error"
        }
        mock_get.return_value = mock_response

        result = AvatarService.download_and_save_avatar(12345, "test_bot_token")
        self.assertIsNone(result)

    def test_get_avatar_url(self):
        """Тест метода get_avatar_url"""
        file_path = "avatars/test_user.png"
        
        # Тест с настройками по умолчанию
        with override_settings(MEDIA_URL='/media/'):
            url = AvatarService.get_avatar_url(file_path)
            self.assertEqual(url, '/media/avatars/test_user.png')

        # Тест без MEDIA_URL
        with override_settings(MEDIA_URL=None):
            url = AvatarService.get_avatar_url(file_path)
            self.assertEqual(url, '/media/avatars/test_user.png')

    def test_delete_old_avatar(self):
        """Тест удаления старой аватарки"""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(b'test content')
            tmp_file_path = tmp_file.name

        try:
            # Тестируем удаление (в тестах просто возвращает True)
            result = AvatarService.delete_old_avatar(12345)
            self.assertTrue(result)
        finally:
            # Очищаем временный файл
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    @patch('user.services.avatar_service.logger')
    def test_download_and_save_avatar_exception_handling(self, mock_logger):
        """Тест обработки исключений"""
        with patch('user.services.avatar_service.requests.get', side_effect=Exception("Test error")):
            result = AvatarService.download_and_save_avatar(12345, "test_bot_token")
            
            self.assertIsNone(result)
            mock_logger.error.assert_called_once()

    def test_image_conversion_to_png(self):
        """Тест конвертации изображения в PNG формат"""
        # Создаем JPEG изображение
        jpeg_image = Image.new('RGB', (50, 50), color='blue')
        jpeg_buffer = BytesIO()
        jpeg_image.save(jpeg_buffer, format='JPEG')
        jpeg_buffer.seek(0)

        # Мокаем requests.get для возврата JPEG изображения
        with patch('user.services.avatar_service.requests.get') as mock_get:
            mock_photos_response = MagicMock()
            mock_photos_response.json.return_value = {
                "ok": True,
                "result": {
                    "photos": [[{"file_id": "test_file_id"}]]
                }
            }

            mock_file_response = MagicMock()
            mock_file_response.json.return_value = {
                "ok": True,
                "result": {
                    "file_path": "photos/test_photo.jpg"
                }
            }

            mock_image_response = MagicMock()
            mock_image_response.status_code = 200
            mock_image_response.content = jpeg_buffer.getvalue()

            mock_get.side_effect = [
                mock_photos_response,
                mock_file_response,
                mock_image_response
            ]

            # Вызываем тестируемый метод
            result = AvatarService.download_and_save_avatar(12345, "test_bot_token")

            # Проверяем, что результат содержит .png расширение
            self.assertIsNotNone(result)
            self.assertTrue(result.endswith('.png'))
