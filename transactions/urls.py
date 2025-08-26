from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # TON кошелек и пополнение
    path('ton/create-address/', views.create_deposit_address, name='create_deposit_address'),
    path('ton/deposit-address/', views.get_deposit_address, name='get_deposit_address'),
    path('ton/balance/', views.get_wallet_balance, name='get_wallet_balance'),
    path('ton/deposit-info/', views.get_deposit_info, name='get_deposit_info'),
    
    # Транзакции
    path('ton/transactions/', views.get_transaction_history, name='get_transaction_history'),
    path('ton/transaction/<str:tx_hash>/', views.get_transaction_status, name='get_transaction_status'),
    path('ton/check-transactions/', views.check_pending_transactions, name='check_pending_transactions'),
]
