# services/top_players.py
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model

User = get_user_model()

def get_top_players(limit=20):
    return (
        User.objects.annotate(
            total_wins_ton=Sum(
                "games_won__pot_amount_ton",
                filter=Q(games_won__status="finished", games_won__mode="pvp"),
                default=0
            ),
            total_wins_stars=Sum(
                "games_won__pot_amount_stars",
                filter=Q(games_won__status="finished", games_won__mode="pvp"),
                default=0
            ),
            wins_count=Count(
                "games_won",
                filter=Q(games_won__status="finished", games_won__mode="pvp")
            ),
        )
        .filter(wins_count__gt=0)
        .order_by("-total_wins_ton")[:limit]
    )
