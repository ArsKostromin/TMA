from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal


class UserManager(BaseUserManager):
    def create_user(self, telegram_id, username=None, **extra_fields):
        if not telegram_id:
            raise ValueError("Telegram ID обязателен")
        user = self.model(
            telegram_id=telegram_id,
            username=username or f"user_{telegram_id}",
            **extra_fields
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id, username=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(telegram_id, username, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    telegram_id = models.BigIntegerField(_("Telegram ID"), unique=True, db_index=True)
    username = models.CharField(_("Username"), max_length=32, blank=True, null=True)
    language_code = models.CharField(_("Lang"), max_length=5, default="ru")
    avatar_url = models.URLField(_("Avatar URL"), blank=True, null=True)

    # Балансы
    balance_ton = models.DecimalField(
        _("TON balance"), max_digits=18, decimal_places=6, default=Decimal("0.0")
    )
    balance_stars = models.PositiveIntegerField(_("Stars balance"), default=0)

    # Розыгрыши / бонусы
    last_daily_participation = models.DateTimeField(_("Last daily join"), blank=True, null=True)
    has_free_test = models.BooleanField(_("Free test active"), default=False)

    # Служебные
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "telegram_id"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["telegram_id"]),
        ]

    def __str__(self):
        return f"{self.username or self.telegram_id}"

    # Балансные операции
    def add_ton(self, amount: Decimal):
        self.balance_ton += Decimal(amount)
        self.save(update_fields=["balance_ton"])

    def subtract_ton(self, amount: Decimal):
        if self.balance_ton < amount:
            raise ValueError("Недостаточно TON")
        self.balance_ton -= Decimal(amount)
        self.save(update_fields=["balance_ton"])

    def add_stars(self, amount: int):
        self.balance_stars += int(amount)
        self.save(update_fields=["balance_stars"])

    def subtract_stars(self, amount: int):
        if self.balance_stars < amount:
            raise ValueError("Недостаточно Stars")
        self.balance_stars -= int(amount)
        self.save(update_fields=["balance_stars"])

    def get_avatar_url(self):
        """Возвращает аватарку пользователя или аватарку по умолчанию"""
        if self.avatar_url:
            return self.avatar_url
        return getattr(settings, 'DEFAULT_AVATAR_URL', "https://teststudiaorbita.ru/media/avatars/diamond.png")
