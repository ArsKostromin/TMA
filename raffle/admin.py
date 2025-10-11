# raffles/admin.py
from django.contrib import admin
from .models import DailyRaffle, DailyRaffleParticipant


class DailyRaffleParticipantInline(admin.TabularInline):
    """
    Встроенная таблица для отображения участников прямо в розыгрыше.
    """
    model = DailyRaffleParticipant
    extra = 0   # не показывать пустых строк
    readonly_fields = ("user", "joined_at")  # участники руками не редактируются
    can_delete = True


@admin.register(DailyRaffle)
class DailyRaffleAdmin(admin.ModelAdmin):
    """
    Админка для управления ежедневными розыгрышами.
    """
    list_display = ("id", "status", "prize", "winner", "started_at", "ends_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "winner__username", "prize__name")
    ordering = ("-created_at",)

    fieldsets = (
        ("Основное", {
            "fields": ("status", "prize", "winner")
        }),
        ("Время", {
            "fields": ("started_at", "ends_at", "created_at", "updated_at")
        }),
    )

    readonly_fields = ("created_at", "updated_at")

    inlines = [DailyRaffleParticipantInline]


@admin.register(DailyRaffleParticipant)
class DailyRaffleParticipantAdmin(admin.ModelAdmin):
    """
    Админка для участников розыгрыша (отдельно, если надо).
    """
    list_display = ("id", "raffle", "user", "joined_at")
    list_filter = ("raffle", "joined_at")
    search_fields = ("user__username", "raffle__id")
    ordering = ("-joined_at",)
