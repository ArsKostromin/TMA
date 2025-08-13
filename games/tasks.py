# tasks.py
from celery import shared_task
from .models import Game

@shared_task
def finish_game_task(game_id):
    from .services.game import GameService
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    game_data = GameService.finish_game(game_id)

    # Отправляем финальное состояние в WS
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"pvp_{game_id}",
        {
            "type": "game_finished",
            **game_data
        }
    )