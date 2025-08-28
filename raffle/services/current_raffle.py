from django.db.models import Count, Exists, OuterRef

from raffle.models import DailyRaffle, DailyRaffleParticipant


def get_current_raffle_with_stats(user):
    """Возвращает активный розыгрыш с аннотациями:
    - participants_count: количество участников
    - user_participates: участвует ли текущий пользователь
    И подгруженным призом через select_related.
    """
    qs = (
        DailyRaffle.objects
        .filter(status="active")
        .order_by("-started_at")
        .select_related("prize")
        .annotate(
            participants_count=Count("participants", distinct=True),
            user_participates=Exists(
                DailyRaffleParticipant.objects.filter(
                    raffle=OuterRef("pk"), user=user
                )
            )
        )
    )

    return qs.first()


