# admin.py
from django.contrib import admin
from .models import User
from gifts.models import Gift
from django.utils.html import format_html


class GiftInline(admin.TabularInline):
    model = Gift
    extra = 0
    fields = ("name", "rarity", "price_ton", "image_preview", "tg_nft_id", "created_at")
    readonly_fields = ("name", "rarity", "price_ton", "image_preview", "tg_nft_id", "created_at")
    can_delete = False
    show_change_link = True

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="40" style="border-radius:4px;"/>', obj.image_url)
        return "—"
    image_preview.short_description = "Превью"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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
    list_filter = ("is_active", "is_staff", "language_code", "date_joined")
    search_fields = ("telegram_id", "username")
    readonly_fields = ("date_joined",)
    ordering = ("-date_joined",)

    fieldsets = (
        ("Основное", {
            "fields": ("telegram_id", "username", "language_code", "avatar_url")
        }),
        ("Балансы", {
            "fields": ("balance_ton", "balance_stars")
        }),
        ("Розыгрыши / бонусы", {
            "fields": ("last_daily_participation", "has_free_test")
        }),
        ("Права", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Служебное", {
            "fields": ("date_joined",)
        }),
    )

    inlines = [GiftInline]
