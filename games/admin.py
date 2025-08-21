# admin.py
from django.contrib import admin
from .models import Game, GamePlayer, SpinGame, SpinWheelSector


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 0
    autocomplete_fields = ["user", "gifts"]
    readonly_fields = ["total_bet_ton", "chance_percent", "joined_at"]
    fields = ["user", "bet_ton", "gifts", "total_bet_ton", "chance_percent", "joined_at"]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "mode", "status", "pot_amount_ton", "winner", "commission_percent", "started_at", "ended_at")
    list_filter = ("mode", "status", "started_at", "ended_at")
    search_fields = ("id", "winner__username", "winner__first_name", "winner__last_name")
    readonly_fields = ("hash", "started_at", "ended_at")
    inlines = [GamePlayerInline]


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "user", "bet_ton", "total_bet_ton", "chance_percent", "joined_at")
    list_filter = ("game__mode", "joined_at")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ["user", "game", "gifts"]
    readonly_fields = ["total_bet_ton"]


@admin.register(SpinGame)
class SpinGameAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "bet_stars", "bet_ton", "win_amount", "gift_won", "result_sector", "played_at")
    list_filter = ("played_at",)
    search_fields = ("player__username", "player__first_name", "player__last_name")
    autocomplete_fields = ["player", "gift_won"]


@admin.register(SpinWheelSector)
class SpinWheelSectorAdmin(admin.ModelAdmin):
    list_display = ("index", "gift", "probability")
    list_filter = ("gift",)
    search_fields = ("gift__name",)
    autocomplete_fields = ["gift"]
    ordering = ["index"]
