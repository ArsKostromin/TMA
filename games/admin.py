from django.contrib import admin
from .models import Game, GamePlayer, SpinGame, SpinWheelSector


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "mode", "status", "pot_amount_ton", "pot_amount_stars", "commission_percent", "winner", "started_at", "ended_at")
    list_filter = ("mode", "status", "started_at")
    search_fields = ("id", "winner__username", "winner__id")
    date_hierarchy = "started_at"
    ordering = ("-started_at",)


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "user", "bet_ton", "bet_stars", "chance_percent", "joined_at")
    list_filter = ("game__mode", "joined_at")
    search_fields = ("user__username", "user__id", "game__id")
    autocomplete_fields = ("game", "user", "gifts")


@admin.register(SpinGame)
class SpinGameAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "bet_stars", "bet_ton", "win_amount", "gift_won", "result_sector", "played_at")
    list_filter = ("played_at", "gift_won")
    search_fields = ("player__username", "player__id")
    autocomplete_fields = ("player", "gift_won")


@admin.register(SpinWheelSector)
class SpinWheelSectorAdmin(admin.ModelAdmin):
    list_display = ("index", "gift", "probability")
    search_fields = ("gift__name",)
    ordering = ("index",)
    autocomplete_fields = ("gift",)
