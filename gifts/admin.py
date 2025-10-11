# gifts/admin.py
from django.contrib import admin
from .models import Gift


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "ton_contract_address",
        "price_ton",
        "rarity_level",
        "is_onchain",
        "created_at",
        "updated_at",
    )
    
    list_filter = (
        "is_onchain",
        "rarity_level",
        "created_at",
        "updated_at",
    )
    
    search_fields = (
        "name",
        "ton_contract_address",
        "user__username",
        "symbol",
        "model_name",
        "pattern_name",
        "backdrop",
    )
    
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "user", "ton_contract_address", "symbol", "price_ton", "rarity_level")
        }),
        ("Визуальные компоненты", {
            "fields": ("model_name", "pattern_name", "backdrop")
        }),
        ("Детали редкости", {
            "fields": (
                ("model_rarity_permille", "model_original_details"),
                ("pattern_rarity_permille", "pattern_original_details"),
                ("backdrop_rarity_permille", "backdrop_original_details"),
            )
        }),
        ("Служебные", {
            "fields": ("is_onchain", "created_at", "updated_at")
        }),
    )
    
    ordering = ("-created_at",)
    save_on_top = True
