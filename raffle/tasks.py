import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django.db import transaction

from raffle.models import DailyRaffle
from gifts.models import Gift

logger = logging.getLogger(__name__)


@shared_task(name="raffle.schedule_raffle_task")
def schedule_raffle_task(raffle_id: int):
    """
    Ставит таску finalize_raffle на момент окончания.
    Используется сигналом post_save.
    """
    raffle = DailyRaffle.objects.filter(id=raffle_id).first()

    if not raffle:
        logger.warning("[RaffleScheduler] raffle %s not found", raffle_id)
        return

    if raffle.status != "active":
        logger.info("[RaffleScheduler] raffle %s is not active -> skip", raffle_id)
        return

    if not raffle.ends_at:
        logger.warning("[RaffleScheduler] raffle %s has no ends_at", raffle_id)
        return

    finalize_raffle.apply_async(
        args=[raffle_id],
        eta=raffle.ends_at
    )

    logger.info("[RaffleScheduler] task scheduled for raffle %s at %s",
                raffle_id, raffle.ends_at)


@shared_task(name="raffle.finalize_raffle")
def finalize_raffle(raffle_id: int):
    """
    Завершает розыгрыш и создаёт следующий.
    """
    logger.info("[Raffle] finalize_raffle triggered for raffle %s", raffle_id)

    with transaction.atomic():
        raffle = (
            DailyRaffle.objects
            .select_related("prize")
            .filter(id=raffle_id, status="active")
            .first()
        )

        if not raffle:
            logger.warning("[Raffle] raffle %s not found or already finished", raffle_id)
            return "not active"

        # ---------- Победитель ----------
        winner = raffle.pick_winner()

        if winner and raffle.prize:
            prize = raffle.prize
            prize.user = winner
            prize.save(update_fields=["user"])
            logger.info("[Raffle] prize %s issued to %s", prize.id, winner.id)

        raffle.status = "finished"
        raffle.save(update_fields=["status", "updated_at"])

        # ---------- Подбор следующего подарка ----------
        current_prize = raffle.prize

        available = Gift.objects.filter(user__isnull=True)

        next_prize = available.exclude(
            pk=current_prize.pk if current_prize else None
        ).order_by("id").first()

        if not next_prize and current_prize:
            next_prize = available.filter(symbol=current_prize.symbol) \
                .exclude(pk=current_prize.pk) \
                .order_by("id") \
                .first()

        if not next_prize:
            logger.warning("[Raffle] no next gift available, stopping chain")
            return "finished, no new raffle created"

        # ---------- Создаём новый ----------
        started_at = timezone.now()
        ends_at = started_at + timedelta(hours=24)

        new_raffle = DailyRaffle.objects.create(
            prize=next_prize,
            status="active",
            started_at=started_at,
            ends_at=ends_at
        )

        logger.info("[Raffle] new raffle %s created", new_raffle.id)

        # ---------- Ставим следующую таску ----------
        finalize_raffle.apply_async(
            args=[new_raffle.id],
            eta=ends_at
        )

        return f"finished raffle {raffle_id}, created new {new_raffle.id}"
