import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from raffle.models import DailyRaffle
from gifts.models import Gift


logger = logging.getLogger(__name__)


def schedule_raffle_job(raffle: DailyRaffle):
    """
    Планирует выполнение process_daily_raffle ровно во время окончания розыгрыша.
    """
    if not raffle.ends_at:
        logger.error("[Raffle] Нельзя запланировать задачу — ends_at отсутствует")
        return

    eta = raffle.ends_at
    process_daily_raffle.apply_async(eta=eta)
    logger.info("[Raffle] Задача завершения розыгрыша %s запланирована на %s",
                raffle.id, eta)


@shared_task(name="raffle.tasks.process_daily_raffle")
def process_daily_raffle() -> str:
    """
    Завершает текущий розыгрыш и создаёт новый, а также планирует следующую задачу.
    Это НЕ периодическая задача — она запускается по ETA в момент окончания розыгрыша.
    """
    logger.info("[Raffle] Запуск process_daily_raffle")

    with transaction.atomic():
        # Берём активный розыгрыш, у которого пришло время завершиться
        raffle = (
            DailyRaffle.objects
            .select_related("prize")
            .filter(status="active", ends_at__lte=timezone.now())
            .order_by("-started_at")
            .first()
        )

        if raffle is None:
            logger.info("[Raffle] Нет активного розыгрыша с истёкшим сроком")
            return "Нет активного розыгрыша с истёкшим сроком"

        # Выбираем победителя
        winner = raffle.pick_winner()

        # Передача подарка
        if winner and raffle.prize:
            prize: Gift = raffle.prize
            prize.user = winner
            prize.save(update_fields=["user"])
            logger.info("[Raffle] Приз %s передан пользователю %s", prize.id, winner.id)
        else:
            logger.info("[Raffle] Приз не выдан (нет победителя или отсутствует приз)")

        # На случай, если pick_winner не закрыл
        if raffle.status != "finished":
            raffle.status = "finished"
            raffle.save(update_fields=["status", "updated_at"])

        # ==== Выбор следующего приза ====
        current_prize = raffle.prize

        available_gifts = Gift.objects.filter(user__isnull=True)

        next_prize = available_gifts.exclude(
            pk=current_prize.pk if current_prize else None
        ).order_by("id").first()

        if not next_prize and current_prize:
            next_prize = available_gifts.filter(
                symbol=current_prize.symbol
            ).exclude(pk=current_prize.pk).order_by("id").first()

        if not next_prize:
            msg = (
                f"Розыгрыш {raffle.id} завершён, "
                f"победитель: {getattr(winner, 'id', None) or 'нет'}, "
                f"новый розыгрыш НЕ создан — нет подарков"
            )
            logger.info("[Raffle] %s", msg)
            return msg

        # ==== Создание нового розыгрыша ====
        started_at = timezone.now()
        ends_at = started_at + timedelta(hours=24)

        new_raffle = DailyRaffle.objects.create(
            prize=next_prize,
            status="active",
            started_at=started_at,
            ends_at=ends_at,
        )

        # === Запланировать задачу завершения ===
        schedule_raffle_job(new_raffle)

        msg = (
            f"Розыгрыш {raffle.id} завершён, "
            f"победитель: {getattr(winner, 'id', None) or 'нет'}, "
            f"создан новый розыгрыш {new_raffle.id}"
        )
        logger.info("[Raffle] %s", msg)
        return msg
