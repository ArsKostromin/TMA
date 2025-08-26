# TON Кошелек и Пополнение Баланса

Этот модуль предоставляет функциональность для пополнения баланса через TON кошелек с поддержкой TON и USDT-TON токенов.

## Основные возможности

- ✅ Генерация уникальных TON адресов для каждого пользователя
- ✅ Поддержка TON и USDT-TON токенов
- ✅ Автоматическая проверка входящих транзакций
- ✅ Отслеживание статуса транзакций
- ✅ API для интеграции с фронтендом
- ✅ Админка для управления кошельками и транзакциями

## Модели данных

### TONWallet
Хранит информацию о TON кошельках пользователей:
- `user` - связь с пользователем
- `address` - адрес кошелька
- `subwallet_id` - ID субкошелька
- `is_active` - активность кошелька

### TONTransaction
Отслеживает TON транзакции:
- `user` - пользователь
- `wallet` - кошелек
- `tx_hash` - хеш транзакции
- `amount` - сумма
- `token` - тип токена (TON/USDT)
- `status` - статус транзакции
- `sender_address` - адрес отправителя

## API Endpoints

### Создание адреса для пополнения
```
POST /api/transactions/ton/create-address/
```
Создает или возвращает существующий адрес для пополнения.

### Получение адреса пополнения
```
GET /api/transactions/ton/deposit-address/
```
Возвращает адрес для пополнения пользователя.

### Получение баланса кошелька
```
GET /api/transactions/ton/balance/
```
Возвращает балансы TON и USDT кошелька.

### Полная информация для пополнения
```
GET /api/transactions/ton/deposit-info/
```
Возвращает полную информацию: адрес, балансы, последние транзакции.

### История транзакций
```
GET /api/transactions/ton/transactions/
```
Возвращает историю TON транзакций пользователя.

### Статус транзакции
```
GET /api/transactions/ton/transaction/{tx_hash}/
```
Возвращает статус конкретной транзакции.

### Проверка транзакций
```
POST /api/transactions/ton/check-transactions/
```
Запускает проверку ожидающих транзакций.

## Команды управления

### Создание кошельков
```bash
# Создать кошелек для конкретного пользователя
python manage.py create_ton_wallets --user-id 123

# Создать кошельки для всех пользователей
python manage.py create_ton_wallets --all

# Создать кошельки только для пользователей без кошельков
python manage.py create_ton_wallets
```

### Проверка транзакций
```bash
# Проверить все активные кошельки
python manage.py check_ton_transactions

# Проверить кошелек конкретного пользователя
python manage.py check_ton_transactions --user-id 123

# Проверить конкретный кошелек
python manage.py check_ton_transactions --wallet-address UQ...
```

## Celery задачи

### Автоматическая проверка транзакций
```python
from transactions.tasks import check_ton_transactions

# Запуск задачи
check_ton_transactions.delay()
```

### Обновление балансов
```python
from transactions.tasks import update_wallet_balances

# Запуск задачи
update_wallet_balances.delay()
```

## Настройка

### 1. Добавьте в settings.py
```python
# TON API настройки
TON_API_BASE_URL = "https://toncenter.com/api/v2"
TON_MASTER_WALLET = "UQDPdsD2e_j6T-CAFNCmcC8fJvQixciaaUgJdK8Xz23taTCV"
USDT_CONTRACT_ADDRESS = "EQB-MPwrd1G6WKNkLz_VnVnY_M9ZR5o0vqa5T8l4bFJXwnaA"
```

### 2. Настройте Celery Beat для автоматической проверки
```python
# В settings.py
CELERY_BEAT_SCHEDULE = {
    'check-ton-transactions': {
        'task': 'transactions.tasks.check_ton_transactions',
        'schedule': 60.0,  # каждые 60 секунд
    },
    'update-wallet-balances': {
        'task': 'transactions.tasks.update_wallet_balances',
        'schedule': 300.0,  # каждые 5 минут
    },
}
```

## Использование в коде

### Создание кошелька для пользователя
```python
from transactions.ton_service import TONService

ton_service = TONService()
wallet = ton_service.create_wallet_for_user(user)
print(f"Адрес кошелька: {wallet.address}")
```

### Получение баланса
```python
ton_balance = ton_service.get_wallet_balance(wallet.address)
usdt_balance = ton_service.check_usdt_balance(wallet.address)
```

### Обработка транзакции
```python
success = ton_service.process_incoming_transaction(tx_data)
if success:
    print("Транзакция обработана успешно")
```

## Безопасность

- Все API endpoints требуют аутентификации
- Транзакции проверяются на уникальность по хешу
- Пользователи могут видеть только свои транзакции
- Админка защищена стандартными Django permissions

## Минимальные суммы пополнения

- TON: 0.1 TON
- USDT: 1.0 USDT

## Поддерживаемые токены

1. **TON** - нативная валюта блокчейна TON
2. **USDT-TON** - стейблкоин USDT в сети TON

## Обработка ошибок

Система автоматически обрабатывает:
- Сетевые ошибки при обращении к TON API
- Дублирование транзакций
- Неверные адреса кошельков
- Ошибки парсинга данных транзакций

## Логирование

Все операции логируются с временными метками:
- Создание кошельков
- Обработка транзакций
- Ошибки API
- Обновление балансов
