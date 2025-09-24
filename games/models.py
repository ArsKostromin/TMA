import random
import hashlib
import secrets
from django.db import models
from django.conf import settings
from decimal import Decimal
from user.models import User


class Game(models.Model):
    MODE_CHOICES = [
        ("pvp", "PVP рулетка"),
        ("spin", "Рекламный спин"),
        ("daily", "Ежедневный розыгрыш"),
    ]

    STATUS_CHOICES = [
        ("waiting", "Ожидание игроков"),
        ("running", "В процессе"),
        ("finished", "Завершена"),
    ]

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="pvp", verbose_name="Режим")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting", verbose_name="Статус")

    pot_amount_ton = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        verbose_name="Общая сумма в TON"
    )

    hash = models.CharField(max_length=64, blank=True, null=True, verbose_name="Hash игры")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало")
    ended_at = models.DateTimeField(blank=True, null=True, verbose_name="Конец")

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="games_won", verbose_name="Победитель"
    )

    commission_percent = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("15.00"),
        verbose_name="Комиссия в %"
    )

    def __str__(self):
        return f"{self.get_mode_display()} — {self.status} ({self.id})"

    def save(self, *args, **kwargs):
        if not self.hash:
            # генерим секрет
            secret = secrets.token_hex(32)
            self.secret = secret
            # кладем в hash
            self.hash = hashlib.sha256(secret.encode()).hexdigest()
        super().save(*args, **kwargs)

    def get_remaining_time(self):
        timer_key = f"game_timer:{self.id}"
        ttl = r.ttl(timer_key)  # вернёт -1 если без таймера, -2 если ключа нет
        return max(ttl, 0)


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players", verbose_name="Игра")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")

    bet_ton = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        verbose_name="Ставка в TON напрямую"
    )

    # Подарки
    gifts = models.ManyToManyField("gifts.Gift", blank=True, verbose_name="Подарки в ставке")

    # Итоговая ставка в TON (подарки + TON)
    total_bet_ton = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        verbose_name="Итоговая ставка в TON"
    )

    chance_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), 
        verbose_name="Шанс победы"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    def recalc_total(self):
        """Пересчитать итоговую ставку (TON + подарки)."""
        gifts_total = self.gifts.aggregate(models.Sum("price_ton"))["price_ton__sum"] or Decimal("0.00")
        self.total_bet_ton = self.bet_ton + gifts_total
        return self.total_bet_ton

    def save(self, *args, **kwargs):# потом лучше изменить
        super().save(*args, **kwargs)   # сначала сохраняем, получаем id
        self.recalc_total()
        super().save(update_fields=["total_bet_ton"])  # второй раз, только total

    def __str__(self):
        return f"{self.user} в игре {self.game_id}"


#режим спин
class SpinGame(models.Model):
    """Конкретная игра игрока"""
    bet_stars = models.PositiveIntegerField(default=0, verbose_name="Ставка в Stars")
    bet_ton = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name="Ставка в TON")
    win_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name="Выигрыш в TON")

    player = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Игрок")
    gift_won = models.ForeignKey(
        "gifts.Gift", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Выигранный подарок"
    )

    result_sector = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Выигрышный сектор")
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Игра Spin"
        verbose_name_plural = "Игры Spin"

    def __str__(self):
        return f"Spin {self.id} для {self.player} ({self.played_at})"


class SpinWheelSector(models.Model):
    """Сектор колеса — подарок и вероятность выпадения"""
    index = models.PositiveSmallIntegerField(verbose_name="Номер сектора")
    gift = models.ForeignKey(
        "gifts.Gift",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Привязанный подарок"
    )
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.0"),
        verbose_name="Вероятность выпадения"
    )

    class Meta:
        unique_together = ("index",)
        verbose_name = "Сектор колеса"
        verbose_name_plural = "Сектора колеса"
        ordering = ["index"]

    def __str__(self):
        return f"Сектор {self.index}: {self.gift or 'Пусто'} (p={self.probability})"