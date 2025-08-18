# admin.py
from django.contrib import admin
from .models import Gift, Inventory
from django.utils.html import format_html


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = (
        "name", "rarity", "price_ton", "is_active",
        "image_preview", "created_at"
    )
    list_filter = ("rarity", "is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at", "image_preview")

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="height:40px; border-radius:6px;" />', obj.image_url)
        return "—"
    image_preview.short_description = "Картинка"


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("user", "gift", "quantity", "acquired_at")
    list_filter = ("gift__rarity", "acquired_at")
    search_fields = ("user__username", "gift__name")
    autocomplete_fields = ("user", "gift")  # удобно искать
    ordering = ("-acquired_at",)
    readonly_fields = ("acquired_at",)
