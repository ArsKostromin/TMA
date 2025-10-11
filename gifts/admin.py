# gifts/admin.py
from django.contrib import admin
from .models import Gift


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "symbol",
        "user",
        "price_ton",
        "rarity",
        "is_onchain",
        "created_at",
    )
    list_filter = ("rarity", "is_onchain", "created_at", "updated_at")
    search_fields = ("name", "symbol", "slug", "tg_nft_id", "ton_contract_address")
    ordering = ("-created_at",)
    list_editable = ("price_ton", "rarity", "is_onchain")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Владение", {
            "fields": ("user",)
        }),
        ("Основная информация", {
            "fields": (
                "name",
                "description",
                "image_url",
                "price_ton",
                "rarity",
            )
        }),
        ("NFT Telegram", {
            "fields": (
                "tg_nft_id",
                "symbol",
                "slug",
                "backdrop",
                "model",
                "ton_contract_address",
                "decimals",
                "is_onchain",
            )
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
        }),
    )
