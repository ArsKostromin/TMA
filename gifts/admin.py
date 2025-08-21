# admin.py
from django.contrib import admin
from .models import Gift
from django.utils.html import format_html


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "rarity",
        "user",
        "price_ton",
        "tg_nft_id",
        "image_preview",
        "created_at",
    )
    list_filter = ("rarity", "created_at", "updated_at")
    search_fields = ("name", "tg_nft_id", "user__username", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at", "image_preview")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("name", "description", "image_url", "image_preview", "price_ton", "rarity")
        }),
        ("Владелец", {
            "fields": ("user", "tg_nft_id")
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="50" style="border-radius:4px;"/>', obj.image_url)
        return "—"
    image_preview.short_description = "Превью"
