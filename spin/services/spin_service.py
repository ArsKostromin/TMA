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
        """Нормализованный коэффициент ставки r ∈ [0..1], учитывает обе валюты (если заданы)."""
        min_stars = Config.get(constants.ROLLS_MIN_STARS, 400, int)
        max_stars = Config.get(constants.ROLLS_MAX_STARS, 50000, int)
        min_ton = Config.get(constants.ROLLS_MIN_TON, Decimal("1.5"), Decimal)
        max_ton = Config.get(constants.ROLLS_MAX_TON, Decimal("50.0"), Decimal)

        if bet_stars:
            denom_s = max(1, (max_stars - min_stars))
            r_stars = _clamp((bet_stars - min_stars) / denom_s)
        else:
            r_stars = 0.0

        if bet_ton and (max_ton > min_ton):
            denom_t = float(max_ton - min_ton)
            r_ton = _clamp((float(bet_ton) - float(min_ton)) / denom_t)
        else:
            r_ton = 0.0

        w_stars = float(Config.get(constants.ROLLS_WEIGHT_W_STARS, Decimal("1.0"), Decimal))
        w_ton = float(Config.get(constants.ROLLS_WEIGHT_W_TON, Decimal("1.0"), Decimal))

        if r_stars and r_ton:
            w_sum = max(1e-9, w_stars + w_ton)
            return _clamp((w_stars * r_stars + w_ton * r_ton) / w_sum)
        elif r_stars:
            return r_stars
        else:
            return r_ton

    @staticmethod
    def _weighted_probabilities(sectors, r: float):
        """Возвращает список весов с учётом ставки."""
        alpha = float(Config.get(constants.ROLLS_WEIGHT_ALPHA, Decimal("0.5"), Decimal))
        gamma = float(Config.get(constants.ROLLS_WEIGHT_GAMMA, Decimal("0.5"), Decimal))

        alpha = max(0.0, alpha)
        gamma = max(1e-6, gamma)

        boost = 1.0 + alpha * (r ** gamma)
        weights = []

        for s in sectors:
            base = float(s.probability)
            if s.gift and s.gift.user is None:
                weights.append(base * boost)
            elif s.gift:
                # если подарок уже занят — шанс 0
                weights.append(0.0)
            else:
                # пустой сектор — шанс 0
                weights.append(0.0)

        # нормализация
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        return weights

    @staticmethod
    def _redistribute_probabilities():
        """Если удалили подарок — перераспределяем шанс на сектор с макс probability."""
        sectors = list(SpinWheelSector.objects.all())
        if not sectors:
            return

        # считаем общую сумму вероятностей и находим максимум
        total_prob = sum(float(s.probability) for s in sectors)
        max_sector = max(sectors, key=lambda s: float(s.probability))

        # считаем сколько “освободилось” (если есть нули)
        active_sum = sum(float(s.probability) for s in sectors if s.gift)
        diff = total_prob - active_sum

        if diff > 0:
            # прибавляем свободный шанс к самому вероятному
            max_sector.probability = Decimal(float(max_sector.probability) + diff)
            max_sector.save(update_fields=["probability"])

    @staticmethod
    def play(user, bet_stars=0, bet_ton=Decimal("0")):
        """Создаёт игру, выбирает сектор, назначает выигрыш, перераспределяет подарки."""
        SpinService.validate_bet(bet_stars, bet_ton)

        if bet_stars > 0:
            user.subtract_stars(bet_stars)
        if bet_ton > 0:
            user.subtract_ton(bet_ton)

        game = SpinGame.objects.create(
            player=user,
            bet_stars=bet_stars,
            bet_ton=bet_ton,
        )

        sectors = list(SpinWheelSector.objects.filter(probability__gt=0))
        if not sectors:
            raise ValidationError(_("Колесо не настроено!"))

        r = SpinService._bet_ratio(bet_stars, bet_ton)
        weights = SpinService._weighted_probabilities(sectors, r)

        chosen = random.choices(sectors, weights=weights, k=1)[0]

        game.result_sector = chosen.index
        game.gift_won = chosen.gift
        game.save(update_fields=["result_sector", "gift_won"])

        # если выиграл подарок
        if chosen.gift:
            won_gift = chosen.gift
            won_gift.user = user
            won_gift.save(update_fields=["user"])

            # ищем аналог (незанятый)
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
                chosen.save(update_fields=["gift"])
            else:
                chosen.gift = None
                chosen.save(update_fields=["gift"])
                # перераспределяем вероятность на жирный сектор
                SpinService._redistribute_probabilities()

            game.gift_won = won_gift
            game.save(update_fields=["gift_won"])

        return game, chosen

    @staticmethod
    def _redistribute_probabilities():
        """Если удалили подарок — перераспределяем шанс на сектор с макс probability."""
        sectors = list(SpinWheelSector.objects.all())
        if not sectors:
            return

        # считаем общую сумму вероятностей
        total_prob = sum(float(s.probability) for s in sectors)
        if total_prob == 0:
            # если все нули — равномерно распределим
            n = len(sectors)
            equal_prob = 1.0 / n
            for s in sectors:
                s.probability = equal_prob
                s.save(update_fields=["probability"])
            return

        # находим сектор с максимальной вероятностью
        max_sector = max(sectors, key=lambda s: float(s.probability))

        # считаем сколько "освободилось" (пустые сектора)
        active_sum = sum(float(s.probability) for s in sectors if s.gift)
        diff = total_prob - active_sum

        if diff > 0:
            # прибавляем освободившуюся вероятность к самому вероятному
            max_sector.probability = Decimal(float(max_sector.probability) + diff)
            max_sector.save(update_fields=["probability"])