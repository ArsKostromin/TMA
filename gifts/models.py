from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils.translation import gettext_lazy as _


class Gift(models.Model):
    RARITY_CHOICES = [
        ("common", "Обычный"),
        ("rare", "Редкий"),
        ("epic", "Эпический"),
        ("legendary", "Легендарный"),
    ]

    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    image_url = models.URLField(verbose_name="Ссылка на изображение")
    price_ton = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        verbose_name="Цена в TON"
    )
    rarity = models.CharField(
        max_length=20, choices=RARITY_CHOICES, default="common",
        verbose_name="Редкость"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен ли в магазине")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"


class Inventory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inventory",
        verbose_name="Пользователь"
    )
    gift = models.ForeignKey(
        Gift, on_delete=models.CASCADE, related_name="inventories",
        verbose_name="Подарок"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    acquired_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата получения")

    class Meta:
        unique_together = ("user", "gift")
        verbose_name = "Инвентарь"
        verbose_name_plural = "Инвентари"

    def __str__(self):
        return f"{self.user} — {self.gift} x{self.quantity}"
