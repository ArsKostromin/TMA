from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class TONWallet(models.Model):
    """Модель для хранения TON кошельков пользователей"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ton_wallet",
        verbose_name="Пользователь"
    )
    
    address = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Адрес кошелька"
    )
    
    subwallet_id = models.IntegerField(
        verbose_name="ID субкошелька"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    
    class Meta:
        verbose_name = "TON Кошелек"
        verbose_name_plural = "TON Кошельки"
    
    def __str__(self):
        return f"TON кошелек {self.user.username}: {self.address}"


class TONTransaction(models.Model):
    """Модель для отслеживания TON транзакций"""
    STATUS_CHOICES = [
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждена"),
        ("failed", "Ошибка"),
    ]
    
    TOKEN_CHOICES = [
        ("TON", "TON"),
        ("USDT", "USDT-TON"),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ton_transactions",
        verbose_name="Пользователь"
    )
    
    wallet = models.ForeignKey(
        TONWallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Кошелек"
    )
    
    tx_hash = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Хеш транзакции"
    )
    
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=9,
        verbose_name="Сумма"
    )
    
    token = models.CharField(
        max_length=10,
        choices=TOKEN_CHOICES,
        default="TON",
        verbose_name="Токен"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Статус"
    )
    
    sender_address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Адрес отправителя"
    )
    
    block_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время блока"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "TON Транзакция"
        verbose_name_plural = "TON Транзакции"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"TON транзакция {self.tx_hash[:10]}... ({self.status})"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("deposit", "Пополнение"),
        ("withdraw", "Вывод"),
        ("bet", "Ставка"),
        ("win", "Выигрыш"),
        ("purchase", "Покупка подарка"),
        ("commission", "Комиссия"),
        ("refund", "Возврат"),
    ]

    CURRENCY_CHOICES = [
        ("TON", "TON"),
        ("USDT", "USDT-TON"),
        ("Stars", "Stars"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Пользователь"
    )

    tx_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Тип транзакции"
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        verbose_name="Сумма"
    )

    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default="TON",
        verbose_name="Валюта"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )
    
    ton_transaction = models.ForeignKey(
        TONTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="app_transactions",
        verbose_name="TON транзакция"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.tx_type in ["deposit", "win", "refund"] else "-"
        return f"{self.user} {sign}{self.amount} {self.currency} ({self.tx_type})"

    @property
    def is_income(self):
        return self.tx_type in ["deposit", "win", "refund"]

    @property
    def is_outcome(self):
        return self.tx_type in ["bet", "purchase", "commission", "withdraw"]
