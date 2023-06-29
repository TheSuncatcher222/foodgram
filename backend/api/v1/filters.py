"""
Создает фильтры для API проекта "Foodgram".

Классы-фильтры:
    - TagsFilter;
    - RecipesFilter.
"""

from django_filters.rest_framework import (
    Filter, FilterSet,
    BooleanFilter, CharFilter)
from rest_framework.exceptions import MethodNotAllowed

from foodgram_app.models import Recipes, RecipesFavorites, ShoppingCarts, User


class TagsFilter(Filter):
    """Вспомогательный фильтр для RecipesFilter, позволяющий вести фильтрацию
    по Many-To-Many полю "tags" модели "Recipes"."""

    def filter(self, queryset, value):
        """Определяет список тегов, которые удовлетворяют введенному(ым)
        значению(ям) поля "name" тега(ов)."""
        if value:
            """При фильтрации теги разделяются символом "_"."""
            tags = value.split('_')
            """Должны быть выданы те рецепты, у которых есть хотя бы
            один из тегов."""
            queryset = queryset.filter(tags__slug__in=tags)
        return queryset


class RecipesFilter(FilterSet):
    """Создает фильтр для "RecipesViewSet".
    Позволяет осуществлять фильтрацию по полям:
        - author;
        - is_favorite: отображает только те рецепты, которые у пользователя
                       добавлены в избранное (есть объект в RecipesFavorites);
        - is_in_shopping_cart: отображает только те рецепты, которые у
                               пользователя добавлены в корзину (есть объект
                               в ShoppingCarts);
        - tags: отображает только те рецепты, для которых определен(ы)
                выбранный(е) тег(и) (через slug).
    """
    author = CharFilter(field_name='author__username')
    is_favorite = BooleanFilter(method='filter_is_favorite')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    tags = TagsFilter(field_name='tags__name')

    class Meta:
        model = Recipes
        fields = ['author', 'is_favorite', 'tags']

    def filter_is_favorite(self, queryset, name, value):
        """Переопределяет queryset: фильтрует только те рецепты, которые
        указаны в RecipesFavorites в паре с текущим пользователем."""

        """Value - это переданное пользователем в запросе значение
        исследуемого поля - "is_favorite"."""
        if not value:
            return queryset
        user: User = self.request.user
        if not user.is_authenticated:
            raise MethodNotAllowed
        recipe_ids: list = RecipesFavorites.objects.filter(
            user=user).values_list('recipe_id', flat=True)
        return Recipes.objects.filter(id__in=recipe_ids)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Переопределяет queryset: фильтрует только те рецепты, которые
        указаны в ShoppingCarts в паре с текущим пользователем."""

        """Value - это переданное пользователем в запросе значение
        исследуемого поля - "is_in_shopping_cart"."""
        if not value:
            return queryset
        user: User = self.request.user
        if not user.is_authenticated:
            raise MethodNotAllowed
        recipe_ids: list = ShoppingCarts.objects.filter(
            user=user).values_list('recipe_id', flat=True)
        return Recipes.objects.filter(id__in=recipe_ids)
