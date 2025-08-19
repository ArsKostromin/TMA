from gifts.models import Inventory

class InventoryService:
    @staticmethod
    def get_user_inventory(user):
        """
        Вернуть QuerySet инвентаря пользователя с предзагрузкой подарков
        """
        return Inventory.objects.filter(user=user).select_related("gift")
