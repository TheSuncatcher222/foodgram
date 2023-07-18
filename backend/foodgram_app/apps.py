from django.apps import AppConfig


class FoodgramAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'foodgram_app'

    def ready(self):
        from .signals import delete_recipe_ingredients, delete_recipe_tags
        return
