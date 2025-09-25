from django.core.exceptions import ValidationError
from django.db import transaction
from games.models import Game, GamePlayer
from gifts.models import Gift
from decimal import Decimal


class BetService:

    @staticmethod
    @transaction.atomic
    def place_bet_gifts(user, game_id, gift_ids: list[int]):
        """
        gift_ids = список Gift.id, которые юзер ставит (каждый Gift уникален)
        """
        try:
            game = (
                Game.objects
                .select_for_update()
                .get(id=game_id)
            )
        except Game.DoesNotExist:
            raise ValidationError("Игра недоступна")

        if game.status == "finished":
            raise ValidationError("Игра уже завершена, ставки не принимаются")

        gp, _ = GamePlayer.objects.get_or_create(game=game, user=user)

        total_added = Decimal("0.00")

        # достаём подарки, которые реально у юзера
        gifts = Gift.objects.select_for_update().filter(id__in=gift_ids, user=user)

        if gifts.count() != len(gift_ids):
            raise ValidationError("Некоторые подарки недоступны для ставки")

        # просто привязываем подарки к игроку в игре
        for gift in gifts:
            gp.gifts.add(gift)
            total_added += gift.price_ton

        # пересчёт общей ставки игрока
        gp.recalc_total()
        gp.save(update_fields=["total_bet_ton"])

        return gp

    @staticmethod
    @transaction.atomic
    def place_bet_ton(user, game_id, amount: Decimal):
        try:
            game = (
                Game.objects
                .select_for_update()
                .get(id=game_id)
            )
        except Game.DoesNotExist:
            raise ValidationError("Игра недоступна")

        if game.status == "finished":
            raise ValidationError("Игра уже завершена, ставки не принимаются")

        if amount <= 0:
            raise ValidationError("Ставка должна быть больше нуля")

        gp, _ = GamePlayer.objects.get_or_create(game=game, user=user)

        # проверка баланса
        if user.balance_ton < amount:
            raise ValidationError("Недостаточно средств на балансе")

        # списываем баланс
        # user.balance_ton -= amount
        # user.save(update_fields=["balance_ton"])

        # добавляем к ставке
        gp.bet_ton += amount
        gp.recalc_total()
        gp.save(update_fields=["bet_ton", "total_bet_ton"])

        return gp
