"""
Создает фильтры для API проекта "Foodgram".

Классы-фильтры:
    - TagsFilter;
    - RecipesFilter.
"""

from django_filters.rest_framework import (
    FilterSet,
    BooleanFilter, CharFilter, ModelMultipleChoiceFilter)
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import BaseFilterBackend

from foodgram_app.models import (
    Recipes, RecipesFavorites, ShoppingCarts, Tags, User)


class IngredientsFilter(BaseFilterBackend):
    """Создает фильтр для "IngredientsViewSet".
    Позволяет осуществлять фильтрацию по полю name: отображает только те
    ингредиенты, которые начинаются с объявленной пользователем записи
    в URL запросе в формате ".../ingredients/?name=..." вне зависимости
    от регистра.
    """

    def filter_queryset(self, request, queryset, view):
        name = request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name.lower())
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
        - tags:
            - отображает только те рецепты, для которых определен(ы)
              выбранный(е) тег(и) (через slug);
            - отображает все рецепты, если фильтр не был указан.
    """

    author = CharFilter(field_name='author__username')
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tags.objects.all())

    class Meta:
        model = Recipes
        fields = ('author', 'is_favorited', 'is_in_shopping_cart', 'tags')

    def _filter_recipes(self, queryset, value, model):
        """Вспомогательная функция. Фильтрует объекты модели "Recipes" согласно
        получаемому списку ID.
        """
        if not value:
            return queryset
        user: User = self.request.user
        if not user.is_authenticated:
            raise MethodNotAllowed
        recipe_ids: list = model.objects.filter(
            user=user).values_list('recipe_id', flat=True)
        return Recipes.objects.filter(id__in=recipe_ids)

    def filter_is_favorited(self, queryset, name, value):
        """Переопределяет queryset: фильтрует только те рецепты, которые
        указаны в RecipesFavorites в паре с текущим пользователем.
        Value - это переданное пользователем в запросе значение
        исследуемого поля - "is_favorited".
        """
        return self._filter_recipes(
            queryset=queryset,
            value=value,
            model=RecipesFavorites)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Переопределяет queryset: фильтрует только те рецепты, которые
        указаны в ShoppingCarts в паре с текущим пользователем.
        Value - это переданное пользователем в запросе значение
        исследуемого поля - "is_in_shopping_cart".
        """
        return self._filter_recipes(
            queryset=queryset,
            value=value,
            model=ShoppingCarts)
