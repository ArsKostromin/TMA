# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Что показываем в списке
    list_display = (
        "id",
        "telegram_id",
        "username",
        "language_code",
        "balance_ton",
        "balance_stars",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "language_code")
    search_fields = ("telegram_id", "username")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_daily_participation")

    # Поля в карточке пользователя
    fieldsets = (
        (None, {"fields": ("telegram_id", "username", "language_code", "avatar_url")}),
        (_("Balances"), {"fields": ("balance_ton", "balance_stars")}),
        (_("Game info"), {"fields": ("last_daily_participation", "has_free_test")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("date_joined", "last_login")}),
    )

    # Для создания через админку
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("telegram_id", "username", "language_code", "is_active", "is_staff", "is_superuser"),
        }),
    )
