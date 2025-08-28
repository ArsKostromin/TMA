from django.db import models
from django.conf import settings
from decimal import Decimal


class Gift(models.Model):
    RARITY_CHOICES = [
        ("common", "Обычный"),
        ("rare", "Редкий"),
        ("epic", "Эпический"),
        ("legendary", "Легендарный"),
    ]

    # --- Владение ---
    # Может быть null, если NFT еще в магазине или не куплен
    # ❗ На проде можно сделать обязательным (null=False, blank=False), если владелец всегда нужен
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gifts",
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    # --- Старое поле, временно оставляем ---
    # ❗ На проде удалить и использовать ton_contract_address + symbol
    tg_nft_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Уникальный ID подарка из ТГ",
        null=True,
        blank=True,
    )

    # --- Базовая инфа о подарке ---
    # ❗ На проде: сделать name обязательным
    name = models.CharField(max_length=255, verbose_name="Название", null=True, blank=True)

    # ❗ Можно оставить необязательным даже в проде
    description = models.TextField(verbose_name="Описание", null=True, blank=True)

    # ❗ На проде: сделать обязательным, без картинки подарок не нужен
    image_url = models.URLField(verbose_name="Ссылка на изображение", null=True, blank=True)

    # ❗ На проде лучше сделать обязательным (default=0 убрать, null=False)
    price_ton = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Цена в TON",
        null=True,
        blank=True,
    )

    # ❗ Может пригодиться только для кастомного магазина, можно убрать при чистке
    rarity = models.CharField(
        max_length=20,
        choices=RARITY_CHOICES,
        default="common",
        verbose_name="Редкость",
        null=True,
        blank=True,
    )

    # --- Поля настоящих NFT Telegram подарков ---
    symbol = models.CharField(
        max_length=50,
        verbose_name="Символ токена (например GFT или TGIFT)",
        null=True,
        blank=True,
    )

    # slug для уникальной ссылки/идентификатора
    slug = models.SlugField(
        max_length=255,
        verbose_name="Slug подарка",
        null=True,
        blank=True,
    )

    # ❗ На проде лучше сделать обязательным, так как в API у подарков всегда есть backdrop
    backdrop = models.URLField(
        verbose_name="Фон (backdrop)",
        null=True,
        blank=True,
    )

    model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Модель (визуальный тип подарка)"
    )

    # TON-адрес смарт-контракта (уникальный идентификатор NFT коллекции)
    ton_contract_address = models.CharField(
        max_length=255,
        verbose_name="TON-адрес смарт-контракта",
        null=True,
        blank=True,
    )

    # ❗ На проде можно сделать обязательным, обычно = 9 для TON NFT
    decimals = models.PositiveIntegerField(
        default=9,
        verbose_name="Десятичные разряды токена",
        null=True,
        blank=True,
    )

    # NFT реально задеплоен в блокчейне или только локально/в магазине
    is_onchain = models.BooleanField(
        default=False,
        verbose_name="Есть ли в блокчейне (onchain)",
    )

    # --- Служебные ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.symbol or 'NFT'})"
        return f"NFT {self.id}"
