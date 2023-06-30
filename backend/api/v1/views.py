import csv

import pandas
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.v1.filters import IngredientsFilter, RecipesFilter
from api.v1.permissions import IsAuthorOrAdminOrReadOnly
from api.v1.serializers import (
    CustomUserSerializer, CustomUserSubscriptionsSerializer,
    IngredientsSerializer, RecipesSerializer, RecipesFavoritesSerializer,
    RecipesShortSerializer, ShoppingCartsSerializer, SubscriptionsSerializer,
    TagsSerializer)
from foodgram_app.models import (
    Ingredients, Tags, Recipes, RecipesFavorites, RecipesIngredients,
    ShoppingCarts, Subscriptions)


@api_view(['POST'])
def csv_import_ingredients(request):
    """Обрабатывает POST-запрос на эндпоинт ".../csv-import/ingredients/":
        - проверяет права доступа: пользователь должен быть администратором;
        - проверяет наличие csv-файла в запросе;
        - производит его валидацию согласно модели "Ingredients";
        - при успешной валидации создает объекты модели "Ingredients."""
    if not request.user.is_staff:
        return Response(
            {'Ошибка': 'Доступ запрещен.'},
            status=status.HTTP_403_FORBIDDEN)
    if request.META.get('CONTENT_TYPE') != 'text/csv':
        return Response(
            {'Ошибка': 'Неправильный тип содержимого. Ожидается text/csv.'},
            status=status.HTTP_400_BAD_REQUEST)
    file = request.FILES.get('file')
    if not file:
        return Response(
            {'Ошибка': 'К запросу не приложен файл.'},
            status=status.HTTP_400_BAD_REQUEST)
    try:
        """Согласно документации, присылаемые файлы не имеют заголовка, и его
        нужно указать вручную при чтении."""
        df = pandas.read_csv(
            file, header=None, names=['name', 'measurement_unit'])
        objects: list = []
        for index, row in df.iterrows():
            objects.append(
                Ingredients(
                    name=row['name'].lower(),
                    measurement_unit=row['measurement_unit']))
        Ingredients.objects.bulk_create(objects)
        return Response({'success': 'CSV file imported successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def custom_user_login(request):
    email: str = request.data.get('email')
    password: str = request.data.get('password')
    if not email or not password:
        return Response(
            {'Ошибка': 'Не указана электронная почта или пароль.'},
            status=status.HTTP_400_BAD_REQUEST)
    user_set = User.objects.filter(email=email)
    if not user_set:
        return Response(
            {'error': 'Неверное указана электронная почта или пароль.'},
            status=status.HTTP_401_UNAUTHORIZED)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Неверное имя пользователя или пароль.'},
            status=status.HTTP_401_UNAUTHORIZED)
    user = authenticate(request, username=user.username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


class CustomUserViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../users/" - предоставляет информацию о пользователях при GET запросе,
                    - создает нового пользователя при POST запросе;
    2) ".../users/{pk}/" - предоставляет информацию о пользователе с ID=pk
                           при GET запросе.
    Дополнительные action-эндпоинты:
    3) ".../users/me/" - предоставляет информацию о текущем пользователе
                         при GET запросе (доступно только
                         авторизированному пользователю);
    4) ".../users/{pk}/subscribe/" - создает подписку на пользователя с ID=pk
                                     при POST запросе;
                                   - удаляет подписку на пользователя с ID=pk
                                     при DELETE запросе;
    5) ".../users/subscriptions/" - предоставляет информацию о пользователях,
                                    на которых осуществлена подписка.
    """
    http_method_names = ('get', 'list', 'post', 'delete')
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    def destroy(self, request, *args, **kwargs):
        """Возвращает статус 405 при попытке совершения DELETE-запроса.
        "Delete" включен явно в перечень разрешенных методов по причине того,
        что он требуется для дочернего @action "subscribe"."""
        raise MethodNotAllowed(request.method)

    def get_queryset(self):
        """Обновляет метод передачи объектов модели в сериализатор:
            - устанавливает сортировку объектов по полю "id"
              (используется встроенная модель "User", в которой явным образом
              не задан мета-параметр "ordering")."""
        return User.objects.prefetch_related(
            'recipe_author').order_by('id')

    @action(detail=False,
            methods=('get',),
            url_path='me',
            permission_classes=(IsAuthenticated,),
            serializer_class=CustomUserSerializer)
    def me(self, request):
        """Добавляет action-эндпоинт ".../users/me/"."""
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=('get',),
            url_path='subscriptions',
            permission_classes=(IsAuthenticated,),
            serializer_class=CustomUserSubscriptionsSerializer)
    def subscriptions(self, request):
        """Добавляет action-эндпоинт ".../users/subscriptions/", возвращающий
        пользователей, на которых подписан текущий пользователь. В выдачу
        добавляются рецепты."""
        subscriptions: Subscriptions = Subscriptions.objects.filter(
            subscriber=request.user).select_related('subscription_to')
        users: list[User] = [subscription.subscription_to
                             for subscription in subscriptions]
        paginator = PageNumberPagination()
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = self.get_serializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=('DELETE', 'POST'),
            url_path=r'(?P<pk>\d+)/subscribe',
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk: int):
        """Добавляет action-эндпоинт ".../users/{pk}/subscribe/":
            - POST: создает подсписку пользователя на автора с id=pk;
            - DELETE: удаляет подписку пользователя на автора с id=pk."""
        subscriber: User = request.user
        subscription_to: User = get_object_or_404(User, id=pk)
        serializer = SubscriptionsSerializer(
            data={'subscriber': subscriber.id,
                  'subscription_to': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        if request.method == 'DELETE':
            Subscriptions.objects.get(
                subscriber=subscriber,
                subscription_to=subscription_to).delete()
            data: None = None
            status_code: status = status.HTTP_204_NO_CONTENT
        elif request.method == 'POST':
            Subscriptions.objects.create(
                subscriber=subscriber,
                subscription_to=subscription_to)
            serializer = CustomUserSubscriptionsSerializer(subscription_to)
            data: dict = serializer.data
            status_code: status = status.HTTP_201_CREATED
        return Response(data=data, status=status_code)


class IngredientsViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../ingredients/"      - предоставляет информацию об ингредиентах
                                 при GET запросе;
    2) ".../ingredients/{pk}/" - предоставляет информацию об ингредиенте
                                 с ID=pk при GET запросе.
    """
    filter_backends = (IngredientsFilter,)
    filterset_fields = ('name',)
    http_method_names = ('get', 'list')
    pagination_class = None
    serializer_class = IngredientsSerializer
    queryset = Ingredients.objects.all()


class RecipesViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../recipes/" - предоставляет информацию о рецептах при GET запросе;
                      - создает рецепт при POST запросе;
    2) ".../recipes/{pk}/" - предоставляет информацию о рецепте с ID=pk
                           - обновляет рецепт при PATCH запросе
                             (доступно только автору рецепта);
                           - удаляет рецепт при DELETE запросе
                             (доступно только автору рецепта).
    Дополнительные action-эндпоинты:
    3) ".../recipes/download_shopping_cart/" - формирует csv файл с элементами
                                               пользовательской корзины.
    """
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    http_method_names = ('delete', 'get', 'list', 'patch', 'post')
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    serializer_class = RecipesSerializer

    def get_queryset(self):
        return Recipes.objects.all().select_related(
            'author').prefetch_related('ingredients', 'tags')

    @action(detail=False,
            methods=('get',),
            url_path='download_shopping_cart',
            permission_classes=(IsAuthenticated,),
            serializer_class=CustomUserSerializer)
    def download_shopping_cart(self, request):
        """Добавляет action-эндпоинт ".../recipes/download_shopping_cart/".
        Формирует "shopping_cart.csv", который содержит в себе данные
        об ингредиентах рецептов в корзине пользователя со столбцами:
            - name: str, название ингредиента;
            - measurement_unit: str, единица измерения ингредиента;
            - amount: float, количество ингредиента."""
        user: User = request.user
        shopping_carts: list[ShoppingCarts] = (
            ShoppingCarts.objects.filter(
                user=user).select_related('recipe'))
        items: dict = {}
        for cart in shopping_carts:
            recipe: Recipes = cart.recipe
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

    @action(detail=False,
            methods=('delete', 'post'),
            url_path=r'(?P<pk>\d+)/favorite',
            permission_classes=(IsAuthenticated,))
    def update_favorite(self, request, pk: int):
        """Добавляет action-эндпоинт ".../recipes/{pk}/favorite/":
            - POST: добавляет рецепт с id=pk в избранное;
            - DELETE: удаляет рецепт с id=pk из избранного."""
        user: User = request.user
        serializer = RecipesFavoritesSerializer(
            data={'user': user.id,
                  'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        recipe: Recipes = Recipes.objects.get(id=pk)
        if request.method == 'DELETE':
            RecipesFavorites.objects.get(recipe=recipe, user=user).delete()
            data: None = None
            status_code: status = status.HTTP_204_NO_CONTENT
        elif request.method == 'POST':
            RecipesFavorites.objects.create(recipe=recipe, user=user)
            serializer = RecipesShortSerializer(instance=recipe)
            data = serializer.data
            status_code: status = status.HTTP_201_CREATED
        return Response(data=data, status=status_code)

    @action(detail=False,
            methods=('delete', 'post'),
            url_path=r'(?P<pk>\d+)/shopping_cart',
            permission_classes=(IsAuthenticated,))
    def update_shopping_cart(self, request, pk: int):
        """Добавляет action-эндпоинт ".../recipes/{pk}/shopping_cart/":
            - POST: добавляет рецепт с id=pk в список покупок;
            - DELETE: удаляет рецепт с id=pk из списка покупок."""
        user: User = request.user
        serializer = ShoppingCartsSerializer(
            data={'user': user.id,
                  'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        recipe: Recipes = Recipes.objects.get(id=pk)
        if request.method == 'DELETE':
            ShoppingCarts.objects.get(recipe=recipe, user=user).delete()
            data: None = None
            status_code: status = status.HTTP_204_NO_CONTENT
        elif request.method == 'POST':
            ShoppingCarts.objects.create(recipe=recipe, user=user)
            serializer = RecipesShortSerializer(instance=recipe)
            data = serializer.data
            status_code: status = status.HTTP_201_CREATED
        return Response(data=data, status=status_code)


class TagsViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) ".../tags/"      - предоставляет информацию о тегах при GET запросе;
    2) ".../tags/{pk}/" - предоставляет информацию о теге с ID=pk
                         при GET запросе.
    """
    http_method_names = ('get', 'list')
    pagination_class = None
    serializer_class = TagsSerializer
    queryset = Tags.objects.all()
