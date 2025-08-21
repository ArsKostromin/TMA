from gifts.models import Gift

class InventoryService:
    @staticmethod
    def get_user_inventory(user):
        """
        Вернуть QuerySet подарков пользователя
        """
        return Gift.objects.filter(user=user).order_by("-created_at")
