import csv

from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.v1.permissions import IsAuthorOrAdminOrReadOnly
from api.v1.serializers import (
    CustomUserSerializer, IngredientsSerializer, RecipesSerializer,
    ShoppingCarts, TagsSerializer)
from footgram_app.models import Ingredients, Tags, Recipes, RecipesIngredients


class CustomUserViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../users/"      - предоставляет информацию о пользователях
                           при GET запросе,
                         - создает нового пользователя при POST запросе;
    2) ".../users/{pk}/" - предоставляет информацию о пользователе с ID=pk
                           при GET запросе.
    Дополнительные action-эндпоинты:
    3) ".../users/me/"   - предоставляет информацию о текущем пользователе
                           при GET запросе (доступно только
                           авторизированному пользователю).
    """
    http_method_names = ('get', 'list', 'post')
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        """Обновляет метод передачи объектов модели в сериализатор:
            - устанавливает сортировку объектов по полю "id"
              (используется встроенная модель "User", в которой явным образом
              не задан мета-параметр "ordering")."""
        queryset = super().get_queryset()
        queryset = queryset.order_by('id')
        return queryset

    @action(detail=False,
            methods=('get',),
            url_path='me',
            permission_classes=(IsAuthenticated,),
            serializer_class=CustomUserSerializer)
    def me(self, request):
        """Добавляет action-эндпоинт `.../users/me/`."""
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class IngredientsViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../ingredients/"     - предоставляет информацию об ингредиентах
                                при GET запросе;
    2) ".../ingredients/{pk}" - предоставляет информацию об ингредиенте
                                с ID=pk при GET запросе.
    """
    http_method_names = ('get', 'list')
    serializer_class = IngredientsSerializer
    queryset = Ingredients.objects.all()


class RecipesViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../recipes/"   - предоставляет информацию о рецептах при GET запросе;
                        - создает рецепт при POST запросе;
    2) ".../tags/{pk}/" - предоставляет информацию о рецепте с ID=pk
                        - обновляет рецепт при PATCH запросе
                          (доступно только автору рецепта);
                        - удаляет рецепт при DELETE запросе
                          (доступно только автору рецепта).
    """
    http_method_names = ('delete', 'get', 'list', 'patch', 'post')
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    serializer_class = RecipesSerializer
    queryset = Recipes.objects.all()

    @action(detail=False,
            methods=('get',),
            url_path='download_shopping_cart',
            permission_classes=(IsAuthenticated,),
            serializer_class=CustomUserSerializer)
    def download_shopping_cart(self, request):
        """Добавляет action-эндпоинт `.../recipes/download_shopping_cart/`.
        Формирует "shopping_cart.csv", который содержит в себе данные
        об ингредиентах рецептов в корзине пользователя со столбцами:
            - name: str, название ингредиента;
            - measurement_unit: str, единица измерения ингредиента;
            - amount: float, количество ингредиента."""
        user: User = request.user
        shopping_carts: list[ShoppingCarts] = (
            ShoppingCarts.objects.filter(
                user=user).select_related('cart_item'))
        items: dict = {}
        for cart in shopping_carts:
            recipe: Recipes = cart.cart_item
            recipes_ingredients: list[RecipesIngredients] = (
                RecipesIngredients.objects.filter(recipe=recipe))
            for recipe_ingredient in recipes_ingredients:
                ingredient = recipe_ingredient.ingredient
                ingredient_name: str = ingredient.name
                if ingredient_name not in items:
                    items[ingredient_name] = {
                        'name': ingredient_name,
                        'measurement_unit': ingredient.measurement_unit,
                        'amount': 0}
                items[ingredient_name]['amount'] += recipe_ingredient.amount
        csv_data: list[tuple[str]] = [('name', 'measurement_unit', 'amount')]
        for ingredient_data in items.values():
            csv_data.append((
                ingredient_data['name'],
                ingredient_data['measurement_unit'],
                ingredient_data['amount'],))
        response: HttpResponse = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"')
        writer: csv = csv.writer(response)
        for row in csv_data:
            writer.writerow(row)
        return response


class TagsViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) `.../tags/      - предоставляет информацию о тегах при GET запросе;
    2) `.../tags/{pk}/ - предоставляет информацию о теге с ID=pk
                         при GET запросе.
    """
    http_method_names = ('get', 'list')
    serializer_class = TagsSerializer
    queryset = Tags.objects.all()
