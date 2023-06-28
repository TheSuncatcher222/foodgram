from django.contrib.admin import site, ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from foodgram_app.models import (
    Ingredients, Recipes, RecipesFavorites, RecipesIngredients,
    RecipesTags, ShoppingCarts, Subscriptions, Tags)


class CustomIngredientsAdmin(ModelAdmin):
    """Создает класс взаимодействия с моделью "Ingredients" в админ-зоне:
        - определяет поля для отображения:
            - "name";
            - "measurement_unit";
        - добавляет фильтрацию по полю "name";
        - добавляет поиск по полям:
            - "name";
            - "measurement_unit"."""
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name', 'measurement_unit')


class CustomRecipesAdmin(ModelAdmin):
    """Создает класс взаимодействия с моделью "Recipes" в админ-зоне:
        - определяет поля для отображения:
            - "name";
            - "cooking_time";
            - "author";
        - добавляет фильтрацию по полям:
            - "name";
            - "cooking_time";
            - "author";
        - добавляет поле "get_favorites_count"."""
    list_display = ('name', 'cooking_time', 'author')
    list_filter = ('name', 'cooking_time', 'tags')
    readonly_fields = ('get_favorites_count',)

    def get_favorites_count(self, obj):
        """Возвращает количество пользователей, которые в настоящий момент
        имеют рецепт в избранном."""
        return RecipesFavorites.objects.filter(recipe=obj).count()

    """Меняет отображение поля в админ-зоне."""
    get_favorites_count.short_description = 'Добавлено в избранное раз'


class CustomUserAdmin(UserAdmin):
    """Переопределяет класс взаимодействия с моделью "User" в админ-зоне:
        - добавляет поиск по полям:
            - "email";
            - "username"."""
    search_fields = ('email', 'username')


site.unregister(User)
site.register(User, admin_class=CustomUserAdmin)

site.register(Ingredients, admin_class=CustomIngredientsAdmin)
site.register(Recipes, admin_class=CustomRecipesAdmin)
site.register(RecipesFavorites)
site.register(RecipesIngredients)
site.register(RecipesTags)
site.register(ShoppingCarts)
site.register(Subscriptions)
site.register(Tags)
