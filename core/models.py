from django.db import models
from decimal import Decimal


class Config(models.Model):
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Ключ настройки"
    )

    value = models.CharField(
        max_length=500,
        verbose_name="Значение"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )

    class Meta:
        verbose_name = "Конфигурация"
        verbose_name_plural = "Конфигурации"

    def __str__(self):
        return f"{self.key} = {self.value}"

    @staticmethod
    def get(key, default=None, cast_type=str):
        try:
            obj = Config.objects.get(key=key)
            return cast_type(obj.value)
        except Config.DoesNotExist:
            return default

    @staticmethod
    def set(key, value):
        obj, _ = Config.objects.get_or_create(key=key)
        obj.value = str(value)
        obj.save()
