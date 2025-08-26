"""
Примеры использования TON API для фронтенда
"""

import requests
import json

# Базовый URL API
BASE_URL = "http://localhost:8000/api/transactions"

# Заголовки с токеном авторизации
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN_HERE",
    "Content-Type": "application/json"
}


def get_deposit_info():
    """Получение информации для пополнения"""
    response = requests.get(f"{BASE_URL}/ton/deposit-info/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("Информация для пополнения:")
        print(f"Адрес кошелька: {data['wallet_address']}")
        print(f"Баланс TON: {data['current_balances']['TON']}")
        print(f"Баланс USDT: {data['current_balances']['USDT']}")
        print(f"Поддерживаемые токены: {data['supported_tokens']}")
        return data
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def create_deposit_address():
    """Создание адреса для пополнения"""
    response = requests.post(f"{BASE_URL}/ton/create-address/", headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        print("Адрес создан:")
        print(f"Адрес: {data['wallet']['address']}")
        return data
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def get_wallet_balance():
    """Получение баланса кошелька"""
    response = requests.get(f"{BASE_URL}/ton/balance/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("Баланс кошелька:")
        print(f"TON: {data['balances']['TON']}")
        print(f"USDT: {data['balances']['USDT']}")
        return data
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def get_transaction_history():
    """Получение истории транзакций"""
    response = requests.get(f"{BASE_URL}/ton/transactions/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("История транзакций:")
        for tx in data['transactions']:
            print(f"Хеш: {tx['tx_hash']}")
            print(f"Сумма: {tx['amount']} {tx['token']}")
            print(f"Статус: {tx['status']}")
            print(f"Дата: {tx['created_at']}")
            print("---")
        return data
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def get_transaction_status(tx_hash):
    """Получение статуса конкретной транзакции"""
    response = requests.get(f"{BASE_URL}/ton/transaction/{tx_hash}/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Статус транзакции {tx_hash}:")
        print(f"Статус: {data['transaction']['status']}")
        print(f"Сумма: {data['transaction']['amount']} {data['transaction']['token']}")
        return data
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def check_pending_transactions():
    """Проверка ожидающих транзакций"""
    response = requests.post(f"{BASE_URL}/ton/check-transactions/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("Проверка транзакций завершена")
        return data
    else:
        print(f"Ошибка: {response.status_code}")
        return None


# Пример использования в JavaScript (fetch)
javascript_example = """
// Получение информации для пополнения
async function getDepositInfo() {
    const response = await fetch('/api/transactions/ton/deposit-info/', {
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token'),
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('Адрес кошелька:', data.wallet_address);
        console.log('Баланс TON:', data.current_balances.TON);
        console.log('Баланс USDT:', data.current_balances.USDT);
        return data;
    } else {
        console.error('Ошибка получения информации');
    }
}

// Создание адреса для пополнения
async function createDepositAddress() {
    const response = await fetch('/api/transactions/ton/create-address/', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token'),
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('Создан адрес:', data.wallet.address);
        return data;
    } else {
        console.error('Ошибка создания адреса');
    }
}

// Получение баланса
async function getWalletBalance() {
    const response = await fetch('/api/transactions/ton/balance/', {
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token'),
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('Баланс TON:', data.balances.TON);
        console.log('Баланс USDT:', data.balances.USDT);
        return data;
    } else {
        console.error('Ошибка получения баланса');
    }
}

// Получение истории транзакций
async function getTransactionHistory() {
    const response = await fetch('/api/transactions/ton/transactions/', {
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token'),
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('Транзакции:', data.transactions);
        return data;
    } else {
        console.error('Ошибка получения истории');
    }
}

// Проверка статуса транзакции
async function getTransactionStatus(txHash) {
    const response = await fetch(`/api/transactions/ton/transaction/${txHash}/`, {
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token'),
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('Статус транзакции:', data.transaction.status);
        return data;
    } else {
        console.error('Ошибка получения статуса');
    }
}
"""

# Пример React компонента
react_component_example = """
import React, { useState, useEffect } from 'react';

const TONWallet = () => {
    const [walletInfo, setWalletInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const getDepositInfo = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/transactions/ton/deposit-info/', {
                headers: {
                    'Authorization': 'Bearer ' + localStorage.getItem('token'),
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setWalletInfo(data);
            } else {
                setError('Ошибка получения информации');
            }
        } catch (err) {
            setError('Сетевая ошибка');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        getDepositInfo();
    }, []);

    if (loading) return <div>Загрузка...</div>;
    if (error) return <div>Ошибка: {error}</div>;
    if (!walletInfo) return <div>Нет данных</div>;

    return (
        <div className="ton-wallet">
            <h2>TON Кошелек</h2>
            
            <div className="wallet-address">
                <h3>Адрес для пополнения:</h3>
                <code>{walletInfo.wallet_address}</code>
                <button onClick={() => navigator.clipboard.writeText(walletInfo.wallet_address)}>
                    Копировать
                </button>
            </div>
            
            <div className="balances">
                <h3>Балансы:</h3>
                <p>TON: {walletInfo.current_balances.TON}</p>
                <p>USDT: {walletInfo.current_balances.USDT}</p>
            </div>
            
            <div className="supported-tokens">
                <h3>Поддерживаемые токены:</h3>
                <ul>
                    {walletInfo.supported_tokens.map(token => (
                        <li key={token}>{token}</li>
                    ))}
                </ul>
            </div>
            
            <div className="recent-transactions">
                <h3>Последние транзакции:</h3>
                {walletInfo.recent_transactions.map(tx => (
                    <div key={tx.id} className="transaction">
                        <p>Хеш: {tx.tx_hash}</p>
                        <p>Сумма: {tx.amount} {tx.token}</p>
                        <p>Статус: {tx.status}</p>
                        <p>Дата: {new Date(tx.created_at).toLocaleString()}</p>
                    </div>
                ))}
            </div>
            
            <button onClick={getDepositInfo}>Обновить</button>
        </div>
    );
};

export default TONWallet;
"""

if __name__ == "__main__":
    print("Примеры использования TON API")
    print("=" * 50)
    
    # Раскомментируйте для тестирования
    # get_deposit_info()
    # create_deposit_address()
    # get_wallet_balance()
    # get_transaction_history()
    # check_pending_transactions()
