from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet

app_name = 'transactions'

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallets')

urlpatterns = [
    path('', include(router.urls)),
]


# urlpatterns = [
#     # Кошельки
#     path('wallets/create/', views.create_wallet, name='create_wallet'),
#     path('wallets/<int:user_id>/', views.get_wallet, name='get_wallet'),
#     path('wallets/<int:user_id>/balance/', views.get_wallet_balance, name='get_wallet_balance'),

#     # Транзакции
#     path('wallets/<int:user_id>/transactions/', views.get_transaction_history, name='transaction_history'),
#     path('transactions/<str:tx_hash>/', views.get_transaction_status, name='transaction_status'),
# ]
