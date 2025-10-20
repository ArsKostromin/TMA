# Используем легковесный базовый образ Python 3.11
FROM python:3.11-slim

# Установка переменных окружения для корректной работы Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копирование файла требований и их установка
COPY requirements.txt /app/

RUN apt-get update && apt-get install -y gcc python3-dev
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего остального кода приложения
# Предполагается, что все файлы (config.py, userbot/, api/) находятся рядом с Dockerfile
COPY . /app

# Указываем порт, который будет слушать FastAPI
EXPOSE 8080

# Команда для запуска приложения (запускает main.py)
CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
