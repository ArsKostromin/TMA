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
        """
        Возвращает список весов с учётом ставки:
        вес призовых секторов умножаем на (1 + ALPHA * r**GAMMA).
        Сектора без гифтов не участвуют, их вероятность перераспределяется.
        """
        alpha = float(Config.get(constants.ROLLS_WEIGHT_ALPHA, Decimal("0.5"), Decimal))   # макс буст = +50%
        gamma = float(Config.get(constants.ROLLS_WEIGHT_GAMMA, Decimal("0.5"), Decimal))   # кривизна (0.5 = sqrt)

        alpha = max(0.0, alpha)
        gamma = max(1e-6, gamma)

        boost = 1.0 + alpha * (r ** gamma)

        weights = []
        for s in sectors:
            base = float(s.probability)
            # бустим только если есть подарок без владельца
            if s.gift and s.gift.user is None:
                weights.append(base * boost)
            else:
                # пустые или выданные подарки = 0
                weights.append(0.0)

        # растягиваем вероятности, если есть пустые
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        return weights


    @staticmethod
    def play(user, bet_stars=0, bet_ton=Decimal("0")):
        """Создаёт игру, выбирает сектор, назначает выигрыш, перераспределяет подарки."""
        SpinService.validate_bet(bet_stars, bet_ton)

        # списываем баланс
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
            # если подарок уже был кем-то взят — скипаем
            if won_gift.user is not None:
                chosen.gift = None
                chosen.save(update_fields=["gift"])
                return game, chosen

            # привязываем к пользователю
            won_gift.user = user
            won_gift.save(update_fields=["user"])

            # ищем замену для этого слота (по имени, редкости и модели)
            replacement = Gift.objects.filter(
                name=won_gift.name,
                rarity_level=won_gift.rarity_level,
                model_name=won_gift.model_name,
                user__isnull=True,
            ).exclude(id=won_gift.id).first()

            if replacement:
                chosen.gift = replacement
                chosen.save(update_fields=["gift"])
            else:
                # очищаем слот
                chosen.gift = None
                chosen.save(update_fields=["gift"])

                # перераспределяем вероятности между нищими гифтовыми секторами
                SpinService._rebalance_probabilities()

            game.gift_won = won_gift
            game.save(update_fields=["gift_won"])

        return game, chosen


    @staticmethod
    def _rebalance_probabilities():
        """
        Если какие-то сектора пустые — перераспределяет их вероятность
        между оставшимися секторами с активными гифтовыми слотами.
        """
        sectors = list(SpinWheelSector.objects.all())
        total_prob = sum(float(s.probability) for s in sectors)
        if total_prob <= 0:
            return

        active = [s for s in sectors if s.gift and s.gift.user is None]
        inactive = [s for s in sectors if not s.gift or (s.gift and s.gift.user is not None)]

        if not active:
            return  # нечего растягивать

        # сколько шанса освободилось
        freed_prob = sum(float(s.probability) for s in inactive)
        if freed_prob <= 0:
            return

        # равномерно добавляем ко всем активным
        add_per_sector = freed_prob / len(active)
        for s in active:
            s.probability = Decimal(float(s.probability) + add_per_sector)
            s.save(update_fields=["probability"])

        # обнуляем пустые
        for s in inactive:
            s.probability = Decimal("0.00")
            s.save(update_fields=["probability"])
