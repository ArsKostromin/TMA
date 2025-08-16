# tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time

@shared_task
def start_timer_task(game_id, duration):
    """
    Сообщаем клиентам, что стартовал таймер.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"pvp_{game_id}",
        {
            "type": "timer_started",
            "duration": duration
        }
    )


@shared_task
def send_timer_task(game_id, duration):
    """
    Каждую секунду шлём оставшееся время.
    """
    channel_layer = get_channel_layer()
    for remaining in range(duration, 0, -1):
        async_to_sync(channel_layer.group_send)(
            f"pvp_{game_id}",
            {
                "type": "timer_update",
                "remaining": remaining
            }
        )
        time.sleep(1)


@shared_task
def finish_game_task(game_id):
    from .services.game import GameService

    game_data = GameService.finish_game(game_id)

    # Отправляем финальное состояние
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"pvp_{game_id}",
        {
            "type": "game_finished",
            **game_data
        }
    )
