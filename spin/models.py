from django.db import models
from django.conf import settings
from decimal import Decimal
from user.models import User


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