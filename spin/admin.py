from django.contrib import admin
from .models import SpinGame, SpinWheelSector


@admin.register(SpinGame)
class SpinGameAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "player",
        "bet_stars",
        "bet_ton",
        "win_amount",
        "gift_won",
        "result_sector",
        "played_at",
    )
    list_filter = ("played_at", "gift_won")
    search_fields = ("player__username", "player__id")
    readonly_fields = ("played_at",)
    ordering = ("-played_at",)

    fieldsets = (
        (None, {
            "fields": ("player", "bet_stars", "bet_ton", "win_amount")
        }),
        ("Результат", {
            "fields": ("gift_won", "result_sector", "played_at")
        }),
    )


@admin.register(SpinWheelSector)
class SpinWheelSectorAdmin(admin.ModelAdmin):
    list_display = ("index", "gift", "probability")
    list_editable = ("gift", "probability")
    search_fields = ("gift__title",)
    ordering = ("index",)
