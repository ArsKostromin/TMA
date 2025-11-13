# games/services/spin.py
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
            min_stars = Config.get(constants.ROLLS_MIN_STARS, 1, int)
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

        # Stars → [0..1]
        if bet_stars:
            denom_s = max(1, (max_stars - min_stars))
            r_stars = _clamp((bet_stars - min_stars) / denom_s)
        else:
            r_stars = 0.0

        # TON → [0..1]
        if bet_ton and (max_ton > min_ton):
            # переводим в float аккуратно — для вероятностей подходит
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
        """Возвращает список весов с учётом ставки:
        вес призовых секторов умножаем на (1 + ALPHA * r**GAMMA)."""
        alpha = float(Config.get(constants.ROLLS_WEIGHT_ALPHA, Decimal("0.5"), Decimal))   # макс буст = +50%
        gamma = float(Config.get(constants.ROLLS_WEIGHT_GAMMA, Decimal("0.5"), Decimal))   # кривизна (0.5 = sqrt)

        # Защита от мусора
        alpha = max(0.0, alpha)
        gamma = max(1e-6, gamma)

        boost = 1.0 + alpha * (r ** gamma)

        weights = []
        for s in sectors:
            base = float(s.probability)
            if s.gift:  # бустим только призовые сектора
                weights.append(base * boost)
            else:
                weights.append(base)
        return weights

    @staticmethod
    def play(user, bet_stars=0, bet_ton=Decimal("0"), game_id=None):
        """
        Создаём игру, учитываем ставку в весах, выбираем сектор, начисляем приз.
        
        Args:
            user: Пользователь
            bet_stars: Ставка в звёздах (уже оплачена через Telegram, не списываем)
            bet_ton: Ставка в TON (списывается только если game_id не указан)
            game_id: ID существующей игры (если игра создана заранее для оплаты)
        """
        SpinService.validate_bet(bet_stars, bet_ton)

        # Списываем только TON (если игра не создана заранее)
        # Звёзды уже списаны Telegram при оплате инвойса
        if game_id:
            # Игра уже создана, просто обновляем её
            game = SpinGame.objects.get(id=game_id, player=user, result_sector__isnull=True)
        else:
            # Создаём новую игру и списываем TON
            if bet_ton > 0:
                user.subtract_ton(bet_ton)
            
            game = SpinGame.objects.create(
                player=user,
                bet_stars=bet_stars,
                bet_ton=bet_ton,
            )

        # Получаем сектора, исключая топовые (с нулевым шансом)
        sectors = list(SpinWheelSector.objects.filter(probability__gt=0))
        if not sectors:
            raise ValidationError(_("Колесо не настроено!"))

        r = SpinService._bet_ratio(bet_stars, bet_ton)
        weights = SpinService._weighted_probabilities(sectors, r)

        chosen = random.choices(sectors, weights=weights, k=1)[0]

        game.result_sector = chosen.index
        game.gift_won = chosen.gift
        game.save(update_fields=["result_sector", "gift_won"])

        # Создаём НОВЫЙ подарок для пользователя на основе выбранного сектора
        if chosen.gift:
            # Используем ton_contract_address как уникальный ID
            new_gift = Gift.objects.create(
                user=user,
                ton_contract_address=f"spin_{game.id}_{chosen.gift.id}",  # уникальный ID для спина
                name=chosen.gift.name,
                image_url=chosen.gift.image_url,
                price_ton=chosen.gift.price_ton,
                rarity_level=getattr(chosen.gift, 'rarity_level', None),
                symbol=getattr(chosen.gift, 'symbol', None),
                model_name=getattr(chosen.gift, 'model_name', None),
                pattern_name=getattr(chosen.gift, 'pattern_name', None),
                backdrop=getattr(chosen.gift, 'backdrop', None),
            )
            # Обновляем игру с новым подарком
            game.gift_won = new_gift
            game.save(update_fields=["gift_won"])

        return game, chosen