from django.db import models
from django.conf import settings
from decimal import Decimal


class Game(models.Model):
    MODE_CHOICES = [
        ("pvp", "PVP рулетка"),
        ("spin", "Рекламный спин"),
        ("daily", "Ежедневный розыгрыш"),
    ]

    status_choices = [
        ("waiting", "Ожидание игроков"),
        ("running", "В процессе"),
        ("finished", "Завершена"),
    ]

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="pvp", verbose_name="Режим")
    status = models.CharField(max_length=20, choices=status_choices, default="waiting", verbose_name="Статус")

    pot_amount_ton = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        verbose_name="Общая сумма в TON"
    )
    pot_amount_stars = models.PositiveIntegerField(default=0, verbose_name="Сумма в Stars")

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


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players", verbose_name="Игра")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")

    bet_ton = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        verbose_name="Ставка в TON"
    )
    bet_stars = models.PositiveIntegerField(default=0, verbose_name="Ставка в Stars")

    # Опционально: если ставили подарки
    gifts = models.ManyToManyField("gifts.Gift", blank=True, verbose_name="Подарки в ставке")

    chance_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name="Шанс победы")

    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} в игре {self.game_id}"


class SpinGame(models.Model):
    sectors_count = models.PositiveSmallIntegerField(default=10, verbose_name="Кол-во секторов")
    bet_ton = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name="Ставка в TON")
    bet_stars = models.PositiveIntegerField(default=0, verbose_name="Ставка в Stars")
    result_sector = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Выигрышный сектор")

    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Игрок")
    gift_won = models.ForeignKey("gifts.Gift", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Выигранный подарок")

    played_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Spin для {self.player} ({self.played_at})"
