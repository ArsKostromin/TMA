#!/usr/bin/env python
"""
Скрипт для проверки доступных подарков в базе данных.
Запускать из корня проекта: python check_gifts.py
"""

import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gifts.models import Gift
from raffle.models import DailyRaffle


def check_gifts():
    """Проверяем доступные подарки"""
    print("=== ПРОВЕРКА ПОДАРКОВ ===")
    
    # Все подарки
    all_gifts = Gift.objects.all()
    print(f"Всего подарков в базе: {all_gifts.count()}")
    
    # Доступные подарки (без владельца)
    available_gifts = Gift.objects.filter(user__isnull=True)
    print(f"Доступных подарков: {available_gifts.count()}")
    
    if available_gifts.exists():
        print("\nДоступные подарки:")
        for gift in available_gifts[:10]:  # Показываем первые 10
            print(f"  ID: {gift.id}, Name: {gift.name}, Symbol: {gift.symbol}, Rarity: {gift.rarity}")
        
        if available_gifts.count() > 10:
            print(f"  ... и еще {available_gifts.count() - 10} подарков")
    else:
        print("❌ Нет доступных подарков!")
    
    # Подарки по символам
    print("\n=== ПОДАРКИ ПО СИМВОЛАМ ===")
    symbols = Gift.objects.values_list('symbol', flat=True).distinct().exclude(symbol__isnull=True)
    for symbol in symbols:
        count = Gift.objects.filter(symbol=symbol).count()
        available_count = Gift.objects.filter(symbol=symbol, user__isnull=True).count()
        print(f"Symbol '{symbol}': {count} всего, {available_count} доступно")
    
    # Подарки без символа
    no_symbol_count = Gift.objects.filter(symbol__isnull=True).count()
    no_symbol_available = Gift.objects.filter(symbol__isnull=True, user__isnull=True).count()
    print(f"Без символа: {no_symbol_count} всего, {no_symbol_available} доступно")


def check_raffles():
    """Проверяем розыгрыши"""
    print("\n=== ПРОВЕРКА РОЗЫГРЫШЕЙ ===")
    
    # Активный розыгрыш
    active_raffle = DailyRaffle.objects.filter(status="active").first()
    if active_raffle:
        print(f"Активный розыгрыш ID: {active_raffle.id}")
        if active_raffle.prize:
            print(f"  Приз: ID={active_raffle.prize.id}, Symbol={active_raffle.prize.symbol}")
        else:
            print("  Приз не задан")
    else:
        print("Нет активного розыгрыша")
    
    # Последние завершенные розыгрыши
    finished_raffles = DailyRaffle.objects.filter(status="finished").order_by('-updated_at')[:3]
    if finished_raffles:
        print("\nПоследние завершенные розыгрыши:")
        for raffle in finished_raffles:
            print(f"  ID: {raffle.id}, Приз: {raffle.prize.id if raffle.prize else 'нет'}, Победитель: {raffle.winner.id if raffle.winner else 'нет'}")


if __name__ == "__main__":
    try:
        check_gifts()
        check_raffles()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


