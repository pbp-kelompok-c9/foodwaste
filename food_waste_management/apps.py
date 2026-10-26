from django.apps import AppConfig


class FoodWasteManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'food_waste_management'

    def ready(self):
        from food_waste_management import signals  # noqa: F401