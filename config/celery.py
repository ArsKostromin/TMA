# config/celery.py
import os
from celery import Celery

# Указываем Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаём приложение Celery
app = Celery('config')

# Загружаем настройки из Django (с префиксом CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем задачи во всех приложениях
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
