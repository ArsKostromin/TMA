# Система аватарок пользователей

## Описание

Система автоматически скачивает аватарки пользователей из Telegram при аутентификации и сохраняет их локально или на S3. Все изображения конвертируются в PNG формат для оптимизации.

## Возможности

- ✅ Автоматическая загрузка аватарок при аутентификации через Telegram
- ✅ Конвертация в PNG формат с оптимизацией
- ✅ Поддержка локального хранения и AWS S3
- ✅ Уникальные имена файлов для предотвращения конфликтов
- ✅ Оптимизация размера изображений (максимум 512x512)
- ✅ Django management команды для управления
- ✅ Полное покрытие тестами

## Установка и настройка

### 1. Зависимости

Убедитесь, что установлены все необходимые пакеты:

```bash
pip install -r requirements.txt
```

### 2. Настройка Django

В `config/settings.py` уже добавлены настройки для медиа файлов:

```python
# Media files (User uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# S3 Configuration (для продакшена)
USE_S3 = os.getenv('USE_S3', 'False').lower() == 'true'
```

### 3. Настройка S3 (опционально)

Для использования AWS S3 добавьте в `.env`:

```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=your-domain.com
```

### 4. Создание директорий

```bash
mkdir -p media/avatars
```

## Использование

### Автоматическая загрузка

Аватарки автоматически загружаются при аутентификации пользователя через Telegram. В `user/services/telegram_auth.py`:

```python
avatar_url = AvatarService.download_and_save_avatar(tg_user["id"], settings.BOT_TOKEN)
```

### Ручное обновление аватарок

Используйте Django management команду:

```bash
# Обновить все аватарки
python manage.py update_avatars

# Обновить аватарку конкретного пользователя
python manage.py update_avatars --user-id 12345

# Принудительно обновить все
python manage.py update_avatars --force
```

### Программное использование

```python
from user.services.avatar_service import AvatarService

# Скачать и сохранить аватарку
avatar_url = AvatarService.download_and_save_avatar(telegram_user_id, bot_token)

# Получить URL аватарки
url = AvatarService.get_avatar_url("avatars/user_123.png")

# Удалить старую аватарку
AvatarService.delete_old_avatar(user_id)
```

## Структура файлов

```
media/
└── avatars/
    ├── user_12345_a1b2c3d4.png
    ├── user_67890_e5f6g7h8.png
    └── ...
```

## API Endpoints

### Аутентификация через Telegram

```
POST /user/telegram-auth/
```

Возвращает:
```json
{
    "id": 1,
    "username": "user123",
    "avatar_url": "/media/avatars/user_12345_a1b2c3d4.png",
    "access": "jwt_token",
    "refresh": "refresh_token"
}
```

## Тестирование

Запустите тесты:

```bash
python manage.py test user.tests.test_avatar_service
```

## Логирование

Система использует стандартное логирование Django. Настройте в `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'user.services.avatar_service': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Производительность

- Изображения оптимизируются до максимального размера 512x512
- Используется PNG формат с оптимизацией
- Уникальные имена файлов предотвращают конфликты
- Поддержка S3 для масштабируемости

## Безопасность

- Валидация входных данных
- Проверка HMAC для Telegram WebApp
- Безопасное хранение файлов
- Логирование всех операций

## Мониторинг

Отслеживайте загрузку аватарок через логи Django и метрики S3 (если используется).

## Troubleshooting

### Ошибка "BOT_TOKEN не настроен"

Проверьте переменную окружения `BOT_TOKEN` в `.env` файле.

### Ошибка загрузки изображения

Проверьте:
- Доступность Telegram Bot API
- Правильность BOT_TOKEN
- Сетевые настройки
- Права доступа к директории media

### Проблемы с S3

Убедитесь, что:
- AWS credentials корректны
- Bucket существует и доступен
- IAM permissions настроены правильно
- CORS настроен для bucket

## Разработка

### Добавление новых форматов

Для поддержки новых форматов изображений отредактируйте метод `download_and_save_avatar` в `AvatarService`.

### Кастомные обработчики

Создайте наследника `AvatarService` для кастомной логики обработки изображений.

## Лицензия

Проект использует стандартную лицензию Django.
