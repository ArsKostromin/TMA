# raffle/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from raffle.models import DailyRaffle
from raffle.tasks import schedule_raffle_task


@receiver(post_save, sender=DailyRaffle)
def schedule_task(sender, instance, created, **kwargs):
    if created:
        schedule_raffle_task.delay(instance.id)
