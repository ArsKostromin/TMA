# # admin.py
# from django.contrib import admin
# from .models import Config


# @admin.register(Config)
# class ConfigAdmin(admin.ModelAdmin):
#     list_display = ("key", "value", "description")   # колонки в списке
#     search_fields = ("key", "value", "description")  # поиск
#     list_filter = ("key",)                           # фильтр по ключу
#     ordering = ("key",)                              # сортировка по ключу
#     list_editable = ("value",)                       # прямо из списка можно менять value
#     save_as = True                                   # "сохранить как новый"
#     save_on_top = True                               # кнопки "сохранить" сверху тоже
