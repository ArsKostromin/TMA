from django.db import models
from django.conf import settings
from decimal import Decimal


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
