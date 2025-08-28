import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from raffle.models import DailyRaffle
from gifts.models import Gift


logger = logging.getLogger(__name__)


@shared_task(name="raffle.tasks.process_daily_raffle")
def process_daily_raffle() -> str:
    """Ежедневное подведение итогов розыгрыша.

    1) Находит активный розыгрыш
    2) Выбирает победителя (если есть участники) и выдаёт приз
    3) Закрывает розыгрыш (status = finished)
    4) Создаёт новый розыгрыш с доступным призом и активирует его

    Возвращает текстовый результат для логов/мониторинга.
    """
    logger.info("[Raffle] Запуск process_daily_raffle")

    with transaction.atomic():
        raffle = (
            DailyRaffle.objects
            .select_related("prize")
            .filter(status="active")
            .order_by("-started_at")
            .first()
        )

        if raffle is None:
            logger.info("[Raffle] Нет активного розыгрыша — ничего не делаем")
            return "Нет активного розыгрыша"

        # Выбор победителя (метод сам закроет розыгрыш, если участников нет)
        winner = raffle.pick_winner()

        # Выдаём приз победителю, если он есть и приз задан
        if winner and raffle.prize:
            prize: Gift = raffle.prize
            prize.user = winner
            prize.save(update_fields=["user"])
            logger.info("[Raffle] Приз %s передан пользователю %s", prize.id, winner.id)
        else:
            if not winner:
                logger.info("[Raffle] Участников не было — победитель отсутствует")
            if not raffle.prize:
                logger.info("[Raffle] Приз для розыгрыша не задан")

        # Закрываем текущий розыгрыш, если метод pick_winner не сделал этого
        if raffle.status != "finished":
            raffle.status = "finished"
            raffle.save(update_fields=["status", "updated_at"])

        # Подбираем приз для следующего розыгрыша
        next_prize: Gift | None = None
        current_prize = raffle.prize
        if current_prize:
            # Ищем свободный подарок такой же коллекции/символа
            next_prize = (
                Gift.objects
                .filter(symbol=current_prize.symbol, user__isnull=True)
                .exclude(pk=current_prize.pk)
                .order_by("id")
                .first()
            )

        if not next_prize:
            logger.info("[Raffle] Нет доступного подарка для следующего розыгрыша — новый не создан")
            result = (
                f"Розыгрыш {raffle.id} завершён, "
                f"победитель: {getattr(winner, 'id', None) or 'нет'}, "
                f"новый розыгрыш не создан (нет подарков)"
            )
            logger.info("[Raffle] %s", result)
            return result

        # Создаём новый розыгрыш на следующие 24 часа
        started_at = timezone.now()
        ends_at = started_at + timedelta(hours=24)
        new_raffle = DailyRaffle.objects.create(
            prize=next_prize,
            status="active",
            started_at=started_at,
            ends_at=ends_at,
        )
        logger.info("[Raffle] Создан новый розыгрыш %s с призом %s", new_raffle.id, next_prize.id)

        result = (
            f"Розыгрыш {raffle.id} завершён, "
            f"победитель: {getattr(winner, 'id', None) or 'нет'}, "
            f"создан новый розыгрыш {new_raffle.id}"
        )
        logger.info("[Raffle] %s", result)
        return result


