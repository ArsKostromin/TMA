# raffles/models.py
import random
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class DailyRaffle(models.Model):
    """
    Модель ежедневного розыгрыша.
    Жизненный цикл: pending → active → finished.
    """

    STATUS_CHOICES = [
        ("pending", "В ожидании"),   # создан, но ещё не запущен
        ("active", "Активен"),       # идёт приём участников
        ("finished", "Завершён"),    # розыгрыш завершён, победитель выбран
    ]

    # Приз — ссылка на Gift (например, NFT-подарок)
    prize = models.ForeignKey(
        "gifts.Gift", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="raffles",
        verbose_name="Приз"
    )

    # Текущий статус розыгрыша
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default="pending", verbose_name="Статус"
    )

    # Когда розыгрыш стартовал
    started_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Время старта"
    )

    # Когда розыгрыш заканчивается (через 24 часа)
    ends_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Время окончания"
    )

    # Кто победил (может быть null, если участников не было)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="raffle_wins",
        verbose_name="Победитель"
    )

    # Технические таймстемпы
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        """
        Проверка: активен ли розыгрыш в данный момент.
        Условие: статус 'active' и время окончания ещё не прошло.
        """
        return self.status == "active" and self.ends_at and self.ends_at > timezone.now()

    def pick_winner(self):
        """
        Логика выбора победителя.
        - Если участников нет → winner=None и статус 'finished'.
        - Если есть → случайно выбираем одного и фиксируем его как победителя.
        """
        participants = list(self.participants.all())
        if not participants:
            # Никто не участвовал → нет победителя
            self.winner = None
            self.status = "finished"
            self.save(update_fields=["winner", "status", "updated_at"])
            return None

        # Рандомный выбор победителя
        winner_entry = random.choice(participants)
        self.winner = winner_entry.user
        self.status = "finished"
        self.save(update_fields=["winner", "status", "updated_at"])
        return self.winner

    def __str__(self):
        return f"Розыгрыш {self.id} — {self.get_status_display()}"


class DailyRaffleParticipant(models.Model):
    """
    Участие конкретного пользователя в розыгрыше.
    Один пользователь может участвовать в одном розыгрыше только один раз.
    """

    # Ссылка на розыгрыш
    raffle = models.ForeignKey(
        DailyRaffle, on_delete=models.CASCADE,
        related_name="participants", verbose_name="Розыгрыш"
    )

    # Ссылка на пользователя
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="raffle_entries", verbose_name="Участник"
    )

    # Когда зашёл в розыгрыш
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ограничение: один пользователь не может дважды зайти в один и тот же розыгрыш
        unique_together = ("raffle", "user")

    def __str__(self):
        return f"{self.user} в розыгрыше {self.raffle_id}"
