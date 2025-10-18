# pyrogram/core/auth_handler.py

import logging
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeEmpty

logger = logging.getLogger(__name__)

async def check_authorization_status(client: Client) -> bool:
    """
    Проверяет, авторизован ли клиент (в Pyrogram это можно сделать через get_me
    или просто через try/except при запуске).
    Здесь мы просто проверим, есть ли информация о пользователе.
    """
    try:
        # Пытаемся получить информацию о себе
        me = await client.get_me()
        return me is not None
    except Exception:
        # Если клиент не запущен/не авторизован, get_me вызовет ошибку
        return False

async def authorize_with_code(client: Client) -> bool:
    """
    Pyrogram автоматически запросит код, если сессии нет.
    Мы просто запускаем цикл ввода данных.
    
    ВНИМАНИЕ: Для реальной работы вам нужно реализовать
    интерактивный ввод с консоли (input()). 
    Здесь мы делаем заглушку, поскольку Pyrogram в режиме Client 
    автоматически выводит запросы в консоль при client.start().
    
    В этом коде мы предполагаем, что запуск client.start()
    в initialize_client сам справится с авторизацией,
    если это первый запуск.
    """
    logger.info("ℹ️ Для первого запуска Pyrogram сам выведет запросы в консоль.")
    return True