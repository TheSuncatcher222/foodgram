"""
Создает сериализаторы моделей проекта "Footgram".

Классы-сериализаторы:
    - CustomUserSerializer (унаследован от UserSerializer)

Создает ограничения для вводимых полей модели:
    - USER_EMAIL_MAX_LEN - максимальная длина поля "email";
    - USER_FIRST_NAME_MAX_LEN - максимальная длина поля "first_name";
    - USER_PASSWORD_MAX_LEN - максимальная длина поля "password";
    - USER_SECOND_NAME_MAX_LEN - максимальная длина поля "second_name";
    - USER_USERNAME_MAX_LEN - максимальная длина поля "username";
    - USER_FORBIDDEN_USERNAMES - список запрещенных значений поля "username";
    - USERNAME_PATTERN - паттерн допустимых символов поля "username".
"""

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from re import sub
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import (
    ModelSerializer,
    EmailField, CharField, SerializerMethodField,
    ValidationError)
from footgram_app.models import (
    Ingredients, Recipes, RecipesFavoritesUsers, RecipesIngredients,
    RecipesTags, ShoppingCarts, Subscriptions, Tags)

USER_EMAIL_MAX_LEN: int = 254
USER_FIRST_NAME_MAX_LEN: int = 150
USER_PASSWORD_MAX_LEN: int = 150
USER_SECOND_NAME_MAX_LEN: int = 150
USER_USERNAME_MAX_LEN: int = 150

USER_FORBIDDEN_USERNAMES: list[str] = ['me']

USERNAME_PATTERN: str = r'^[\w.@+-]+$'


class CustomUserSerializer(UserSerializer):
    """Переопределяет UserSerializer библиотеки Djoser:
        - добавляет поле 'is_subscribed' в конец списка полей;
        - делает обязательными для заполнения поля:
            - 'email';
            - 'first_name';
            - 'last_name';
        - производит валидацию на уникальность поля 'email'."""
    email = EmailField(max_length=USER_EMAIL_MAX_LEN)
    is_subscribed = SerializerMethodField()
    password = CharField(
        max_length=USER_PASSWORD_MAX_LEN,
        write_only=True)
    username = CharField(max_length=USER_USERNAME_MAX_LEN)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'required': True}}

    def get_is_subscribed(self, obj):
        """Показывает статус подписки пользователя в поле 'is_subscribed'.
        Возвращает True, если пользователь имеет подписку, False - если не
        имеет, или пользователь не авторизован."""
        user: User = self.context['request'].user
        if user.is_anonymous:
            return False
        else:
            return Subscriptions.objects.filter(
                subscriber=user,
                subscription_to=obj).exists()

    def validate_email(self, value):
        """Производит валидацию поля 'email':
            - проверяет на уникальность."""
        if User.objects.filter(email=value).exists():
            raise ValidationError(
                'Пользователь с такой электронной почтой уже существует.')
        return value

    def validate_username(self, value):
        """Производит валидацию поля 'email':
            - проверяет на уникальность;
            - проверяет на несоответствие запрещенным именам."""
        forbidden_chars: str = sub(
            pattern=USERNAME_PATTERN,
            repl='',
            string=value)
        if forbidden_chars:
            sort_chars: str = ', '.join(
                f'"{c}"' for c in sorted(set(forbidden_chars)))
            raise ValidationError(
                f'Использование {sort_chars} в имени пользователя запрещено.')
        for forbidden in USER_FORBIDDEN_USERNAMES:
            if value.lower() == forbidden.lower():
                raise ValidationError(
                    f'Пользователь с именем "{forbidden}" недопустим.')
        if User.objects.filter(username=value).exists():
            raise ValidationError(
                'Пользователь с таким именем уже существует.')
        return value


class IngredientsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Ingredients"."""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit')


class TagsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Tags"."""

    class Meta:
        model = Tags
        fields = (
            'id',
            'name',
            'color',
            'slug')


class RecipesSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes"."""

    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsSerializer(many=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    is_subscribed = SerializerMethodField()
    tags = TagsSerializer(many=True)

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time')
        read_only_fields = ('author',)

    def create(self, validated_data):
        """Переопределяет метод сохранения данных, включает инструкции
        по работе со связными сериализаторами:
            - "ingredients": "IngredientsSerializer";
            - "tags": "TagsSerializer"."""
        validated_data['author'] = self.context['request'].user
        ingredients: list = validated_data.pop('ingredients')
        tags: list = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        for ingredient in ingredients:
            # ToDo: проверить, что тут происходит и можно ли применить метод:
            # ingredient = ingredient.title()
            current_ingredient, _ = (
                Ingredients.objects.get_or_create(**ingredient))
            RecipesIngredients.objects.create(
                recipe=recipe, ingredient=current_ingredient)
        for tag in tags:
            current_tag, _ = Tags.objects.get_or_create(**tag)
            RecipesTags.objects.create(recipe=recipe, tag=current_tag)
        return recipe

    def get_is_favorited(self, obj):
        """Показывает наличие рецепта в избранном пользователя в поле
        'is_subscribed'. Возвращает True, если рецепт в избранном,
        False - если нет."""
        return RecipesFavoritesUsers.objects.filter(
            user=self.context['request'].user,
            recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Показывает наличие рецепта в корзине пользователя в поле
        'is_in_shopping_cart'. Возвращает True, если рецепт в корзине,
        False - если нет."""
        return ShoppingCarts.objects.filter(
            user=self.context['request'].user,
            cart_item=obj).exists()

    # ToDo: проверить необходимость кода:
    # def perform_create(self, serializer):
    #     """Дополняет метод save() для записи в БД:
    #         - добавляет пользователя из запроса в поле "author"."""
    #     serializer.save(author=self.request.user)
    #     return


class RecipesFavoritesUsersSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes" в случае, если происходит
    добавление рецепта в избранное или удаление его оттуда."""

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time')

    def create(self, serializer):
        """Дополняет метод save() для записи в БД:
            - добавляет запись в таблицу "RecipesFavoritesUsers"."""
        recipe_id = self.kwargs['id']
        recipe: Recipes = get_object_or_404(Recipes, id=recipe_id)
        user: User = self.request.user
        if RecipesFavoritesUsers.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка добавления в избранное. '
                'Рецепт уже находится в избранном.')
        RecipesFavoritesUsers.objects.create(recipe=recipe, user=user)
        return

    def destroy(self, request, *args, **kwargs):
        """Дополняет метод destroy() для удаления из БД:
            - удаляет запись из таблицы "RecipesFavoritesUsers"."""
        recipe_id: int = self.kwargs['pk']
        recipe: Recipes = get_object_or_404(Recipes, id=recipe_id)
        user: User = self.request.user
        if not RecipesFavoritesUsers.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка удаления из избранного. '
                'Рецепта нет в избранном.')
        recipe_favorite: RecipesFavoritesUsers = get_object_or_404(
            RecipesFavoritesUsers, recipe=recipe_id, user=user)
        recipe_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
