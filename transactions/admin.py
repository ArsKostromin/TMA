# from django.contrib import admin
# from .models import Transaction, TONWallet, TONTransaction


# @admin.register(TONWallet)
# class TONWalletAdmin(admin.ModelAdmin):
#     list_display = ['user', 'address', 'subwallet_id', 'is_active', 'created_at']
#     list_filter = ['is_active', 'created_at']
#     search_fields = ['user__username', 'user__email', 'address']
#     readonly_fields = ['created_at']
    
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('user', 'address', 'subwallet_id')
#         }),
#         ('Статус', {
#             'fields': ('is_active',)
#         }),
#         ('Даты', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         }),
#     )


# @admin.register(TONTransaction)
# class TONTransactionAdmin(admin.ModelAdmin):
#     list_display = ['user', 'tx_hash', 'amount', 'token', 'status', 'created_at']
#     list_filter = ['status', 'token', 'created_at']
#     search_fields = ['user__username', 'tx_hash', 'sender_address']
#     readonly_fields = ['created_at', 'updated_at']
    
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('user', 'wallet', 'tx_hash', 'amount', 'token')
#         }),
#         ('Статус и детали', {
#             'fields': ('status', 'sender_address', 'block_time')
#         }),
#         ('Даты', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )


# @admin.register(Transaction)
# class TransactionAdmin(admin.ModelAdmin):
#     list_display = ['user', 'tx_type', 'amount', 'currency', 'created_at']
#     list_filter = ['tx_type', 'currency', 'created_at']
#     search_fields = ['user__username', 'description']
#     readonly_fields = ['created_at']
    
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('user', 'tx_type', 'amount', 'currency', 'description')
#         }),
#         ('TON транзакция', {
#             'fields': ('ton_transaction',),
#             'classes': ('collapse',)
#         }),
#         ('Даты', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         }),
#     )
