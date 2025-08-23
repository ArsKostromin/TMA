from django.db.models import Prefetch
from games.models import Game, GamePlayer


def get_last_pvp_winner():
    """
    Возвращает (game, GamePlayer победителя) для последней pvp-игры.
    Если ничего не найдено — None, None.
    """

    last_game = (
        Game.objects
        .filter(mode="pvp", status="finished")
        .order_by("-ended_at", "-id")
        .select_related("winner")
        .first()
    )

    if not last_game or not last_game.winner_id:
        return None, None

    winner_gp = (
        GamePlayer.objects
        .select_related("user", "game")
        .only(
            "total_bet_ton",
            "chance_percent",
            "user__id",
            "user__username",
            "user__avatar_url",
            "game__pot_amount_ton",
            "game__commission_percent"
        )
        .filter(game=last_game, user=last_game.winner)
        .first()
    )

    return last_game, winner_gp
