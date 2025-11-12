from decimal import Decimal
from django.db import transaction
from spin.models import SpinGame
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SpinService:
    @staticmethod
    def create_spin_game(user, bet_stars: int = 0, bet_ton: Decimal = Decimal("0.00")):
        """
        Создаёт новую индивидуальную игру (SpinGame) для пользователя.
        """
        with transaction.atomic():
            game = SpinGame.objects.create(
                player=user,
                bet_stars=bet_stars,
                bet_ton=bet_ton,
                played_at=timezone.now(),
            )
            logger.info(f"Создан SpinGame #{game.id} для пользователя {user.username}, ставка {bet_ton} TON / {bet_stars} Stars")

        return game.id, f"spin_{game.id}"
