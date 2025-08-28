from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from games.models import GamePlayer
from raffle.models import DailyRaffle, DailyRaffleParticipant


def user_played_last_24h(user) -> bool:
    """Есть ли участие пользователя в играх за последние 24 часа."""
    since = timezone.now() - timedelta(hours=24)
    return GamePlayer.objects.filter(user=user, joined_at__gte=since).exists()


def join_current_raffle(user):
    """Пытается добавить пользователя в активный розыгрыш.

    Возвращает кортеж (code, data):
    - ("no_active", None) — нет активного розыгрыша
    - ("forbidden", None) — пользователь не играл за последние 24 часа
    - ("conflict", None) — уже участвует
    - ("created", participant) — успешно добавлен
    """
    raffle = (
        DailyRaffle.objects
        .filter(status="active")
        .order_by("-started_at")
        .first()
    )
    if raffle is None:
        return "no_active", None

    if not user_played_last_24h(user):
        return "forbidden", None

    try:
        with transaction.atomic():
            participant, created = DailyRaffleParticipant.objects.get_or_create(
                raffle=raffle,
                user=user,
            )
    except IntegrityError:
        return "conflict", None

    if not created:
        return "conflict", None

    return "created", participant


