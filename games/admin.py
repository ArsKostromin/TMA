from django.contrib import admin
from .models import Game, GamePlayer, SpinGame


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 0
    readonly_fields = ("user", "bet_ton", "bet_stars", "chance_percent", "joined_at")
    can_delete = False


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "id", "mode", "status", "pot_amount_ton", "pot_amount_stars",
        "winner", "commission_percent", "started_at", "ended_at"
    )
    list_filter = ("mode", "status", "started_at", "ended_at")
    search_fields = ("id", "hash", "winner__username", "winner__telegram_id")
    readonly_fields = ("started_at", "ended_at", "hash")
    inlines = [GamePlayerInline]


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = (
        "id", "game", "user", "bet_ton", "bet_stars", "chance_percent", "joined_at"
    )
    list_filter = ("joined_at", "chance_percent")
    search_fields = ("user__username", "user__telegram_id", "game__id")


@admin.register(SpinGame)
class SpinGameAdmin(admin.ModelAdmin):
    list_display = (
        "id", "player", "sectors_count", "bet_ton", "bet_stars",
        "result_sector", "gift_won", "played_at"
    )
    list_filter = ("sectors_count", "played_at")
    search_fields = ("player__username", "player__telegram_id")
    readonly_fields = ("played_at",)
