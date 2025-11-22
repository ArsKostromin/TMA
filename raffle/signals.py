from django.db.models.signals import post_save
from django.dispatch import receiver
from raffle.models import DailyRaffle
from raffle.tasks import finalize_raffle

@receiver(post_save, sender=DailyRaffle)
def schedule_task(sender, instance, created, **kwargs):
    if created and instance.ends_at:
        finalize_raffle.apply_async(eta=instance.ends_at)
