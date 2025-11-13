# games/services/spin_service.py
import math
import random
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from spin.models import SpinGame, SpinWheelSector
from gifts.models import Gift
from core.models import Config
from core import constants


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


class SpinService:
    @staticmethod
    def validate_bet(bet_stars, bet_ton):
        if bet_stars:
            min_stars = Config.get(constants.ROLLS_MIN_STARS, 400, int)
            max_stars = Config.get(constants.ROLLS_MAX_STARS, 50000, int)
            if not (min_stars <= bet_stars <= max_stars):
                raise ValidationError(_(f"Ставка в Stars должна быть от {min_stars} до {max_stars}"))

        if bet_ton:
            min_ton = Config.get(constants.ROLLS_MIN_TON, Decimal("1.5"), Decimal)
            max_ton = Config.get(constants.ROLLS_MAX_TON, Decimal("50.0"), Decimal)
            if not (min_ton <= bet_ton <= max_ton):
                raise ValidationError(_(f"Ставка в TON должна быть от {min_ton} до {max_ton}"))

        if not bet_stars and not bet_ton:
            raise ValidationError(_("Нужна ставка в Stars или TON"))

    @staticmethod
    def _bet_ratio(bet_stars: int, bet_ton: Decimal) -> float:
        min_stars = Config.get(constants.ROLLS_MIN_STARS, 400, int)
        max_stars = Config.get(constants.ROLLS_MAX_STARS, 50000, int)
        min_ton = Config.get(constants.ROLLS_MIN_TON, Decimal("1.5"), Decimal)
        max_ton = Config.get(constants.ROLLS_MAX_TON, Decimal("50.0"), Decimal)

        r_stars = _clamp((bet_stars - min_stars) / max(1, max_stars - min_stars)) if bet_stars else 0.0
        r_ton = _clamp((float(bet_ton) - float(min_ton)) / float(max_ton - min_ton)) if bet_ton else 0.0

        w_stars = float(Config.get(constants.ROLLS_WEIGHT_W_STARS, Decimal("1.0"), Decimal))
        w_ton = float(Config.get(constants.ROLLS_WEIGHT_W_TON, Decimal("1.0"), Decimal))

        if r_stars and r_ton:
            return _clamp((w_stars * r_stars + w_ton * r_ton) / max(1e-9, w_stars + w_ton))
        return r_stars or r_ton

    @staticmethod
    def _weighted_probabilities(sectors, r: float):
        """Весовые коэффициенты с учётом ставки."""
        alpha = float(Config.get(constants.ROLLS_WEIGHT_ALPHA, Decimal("0.5"), Decimal))
        gamma = float(Config.get(constants.ROLLS_WEIGHT_GAMMA, Decimal("0.5"), Decimal))
        boost = 1.0 + max(0.0, alpha) * (r ** max(1e-6, gamma))

        weights = []
        for s in sectors:
            base = float(s.probability)
            if s.gift and s.gift.user is None:
                weights.append(base * boost)
            else:
                weights.append(0.0)

        if sum(weights) == 0:
            n = len(sectors)
            weights = [1.0 / n] * n

        total = sum(weights)
        return [w / total for w in weights]

    @staticmethod
    def play(user, bet_stars=0, bet_ton=Decimal("0")):
        SpinService.validate_bet(bet_stars, bet_ton)

        if bet_stars > 0:
            user.subtract_stars(bet_stars)
        if bet_ton > 0:
            user.subtract_ton(bet_ton)

        game = SpinGame.objects.create(player=user, bet_stars=bet_stars, bet_ton=bet_ton)

        sectors = list(SpinWheelSector.objects.filter(probability__gt=0))
        if not sectors:
            raise ValidationError(_("Колесо не настроено!"))

        r = SpinService._bet_ratio(bet_stars, bet_ton)
        weights = SpinService._weighted_probabilities(sectors, r)
        chosen = random.choices(sectors, weights=weights, k=1)[0]

        game.result_sector = chosen.index
        game.gift_won = chosen.gift
        game.save(update_fields=["result_sector", "gift_won"])

        if chosen.gift:
            won_gift = chosen.gift
            won_gift.user = user
            won_gift.save(update_fields=["user"])

            replacement = Gift.objects.filter(
                name=won_gift.name,
                image_url=won_gift.image_url,
                ton_contract_address=won_gift.ton_contract_address,
                price_ton=won_gift.price_ton,
                rarity_level=won_gift.rarity_level,
                user__isnull=True,
            ).exclude(id=won_gift.id).first()

            if replacement:
                chosen.gift = replacement
            else:
                chosen.gift = None
                SpinService._redistribute_probabilities(chosen)

            chosen.save(update_fields=["gift"])
            game.gift_won = won_gift
            game.save(update_fields=["gift_won"])

        return game, chosen

    @staticmethod
    def _redistribute_probabilities(removed_sector):
        """Перераспределяем вероятность после того, как подарок удалён.
        Логика:
        - обнуляем вероятность сектора, с которого забрали подарок
        - находим сектор с максимальной вероятностью, который ещё содержит подарок
        - добавляем к нему освобождённую вероятность
        """
        sectors = list(SpinWheelSector.objects.all())
        if not sectors:
            return

        # забираем текущую вероятность сектора и обнуляем её
        removed_prob = float(removed_sector.probability)
        removed_sector.probability = 0.0
        removed_sector.save(update_fields=["probability"])

        # ищем сектор с максимальной вероятностью, который ещё содержит подарок
        active_sectors = [s for s in sectors if s.gift is not None and s.id != removed_sector.id]
        if not active_sectors:
            # если нет активных секторов — ничего не делаем
            return

        max_sector = max(active_sectors, key=lambda s: float(s.probability))
        max_sector.probability = Decimal(float(max_sector.probability) + removed_prob)
        max_sector.save(update_fields=["probability"])