from django.db import models
from django.conf import settings
from decimal import Decimal


class Gift(models.Model):
    # --- Владение (Сохранено) ---
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gifts",
        verbose_name="Владелец",
        null=True,
        blank=True,
    )
    
    # --- Базовая инфа о подарке ---
    # name: Название + Номер NFT (Lunar Snake #97546)
    name = models.CharField(max_length=255, verbose_name="Название")
    
    # image_url: Ссылка на стикер .tgs (Обязательное)
    image_url = models.URLField(verbose_name="Ссылка на изображение")
    
    # price_ton: Цена в TON (Оставлено как Decimal, но null=True/blank=True, т.к. может быть подарком/не из магазина)
    price_ton = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Цена в TON",
        null=True,
        blank=True,
    )
    
    # rarity: Общий уровень редкости (Standard, Rare и т.д.)
    rarity_level = models.CharField(
        max_length=50,
        verbose_name="Общий уровень редкости (TG)",
        null=True,
        blank=True,
    )
    
    # --- Идентификаторы TON / Telegram (Обязательные) ---
    
    # ton_contract_address: Уникальный slug/ID (LunarSnake-97546). Используем как главный ID.
    ton_contract_address = models.CharField(
        max_length=255,
        unique=True,  # Делаем уникальным
        verbose_name="TON-адрес / Уникальный ID (Slug)",
    )

    # symbol: (Оставлено, но может быть null, т.к. для NFT-подарков это может быть пусто)
    symbol = models.CharField(
        max_length=50,
        verbose_name="Символ токена",
        null=True,
        blank=True,
    )
    
    # --- Визуальные компоненты (Извлекаются из Telegram) ---
    
    # backdrop: Фон/цвет (например, Aquamarine)
    backdrop = models.CharField(
        max_length=100,
        verbose_name="Название фона (Backdrop)",
        null=True,
        blank=True,
    )
    
    # model: Визуальный тип подарка (например, Candy Stripe)
    model_name = models.CharField(
        max_length=100,
        verbose_name="Модель (визуальный тип)",
        null=True,
        blank=True,
    )

    # pattern: Узор/текстура (например, Stocking)
    pattern_name = models.CharField(
        max_length=100,
        verbose_name="Название узора (Pattern)",
        null=True,
        blank=True,
    )

    # --- Детали редкости (Новые поля) ---
    
    # Model Rarity
    model_rarity_permille = models.PositiveSmallIntegerField(
        verbose_name="Редкость Модели (permille)",
        null=True,
        blank=True,
    )
    model_original_details = models.JSONField(
        verbose_name="Original Details Модели",
        null=True,
        blank=True,
    )

    # Pattern Rarity
    pattern_rarity_permille = models.PositiveSmallIntegerField(
        verbose_name="Редкость Узора (permille)",
        null=True,
        blank=True,
    )
    pattern_original_details = models.JSONField(
        verbose_name="Original Details Узора",
        null=True,
        blank=True,
    )
    
    # Backdrop Rarity
    backdrop_rarity_permille = models.PositiveSmallIntegerField(
        verbose_name="Редкость Фона (permille)",
        null=True,
        blank=True,
    )
    backdrop_original_details = models.JSONField(
        verbose_name="Original Details Фона",
        null=True,
        blank=True,
    )


    # --- Служебные / Очищенные ---
    is_onchain = models.BooleanField(
        default=False,
        verbose_name="Есть ли в блокчейне (onchain)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # #для отправки подарка пользователю
    # peer_id = models.BigIntegerField(
    #     verbose_name="Редкость Фона (permille)",
    #     null=True,
    #     blank=True,
    #     help_text="Используется для InvokeWithMsgId при дарении гифта"
    # )
    # msg_id = models.BigIntegerField(
    #     verbose_name="ID сообщения с подарком (msg_id)",
    #     null=True,
    #     blank=True,
    #     help_text="ID конкретного сообщения, где лежит подарок"
    # )
    # access_hash = models.BigIntegerField(
    #     verbose_name="Access Hash чата (access_hash)",
    #     null=True,
    #     blank=True,
    #     help_text="Нужен для доступа к чату/пользователю через Telethon"
    # )
    # sender_id = models.BigIntegerField(
    #     verbose_name="ID пользователя, приславшего подарок (sender_id)",
    #     null=True,
    #     blank=True,
    #     help_text="Telegram ID отправителя гифта"
    # )
    # chat_name = models.CharField(
    #     max_length=255,
    #     verbose_name="Название чата или имя источника (chat_name)",
    #     null=True,
    #     blank=True,
    #     help_text="Имя чата, откуда пришёл подарок"
    # )
    
    class Meta:
        verbose_name = "NFT Подарок"
        verbose_name_plural = "NFT Подарки"
        # Убеждаемся, что уникальность гарантируется основным ID
        constraints = [
            models.UniqueConstraint(fields=['ton_contract_address'], name='unique_tg_nft_id')
        ]

    def __str__(self):
        return f"{self.name} ({self.ton_contract_address or 'NFT'})"