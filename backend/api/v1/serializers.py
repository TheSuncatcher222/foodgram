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
    CharField, EmailField, FloatField, IntegerField, ListField, ReadOnlyField,
    SerializerMethodField,
    ValidationError)
from footgram_app.models import (
    Ingredients, Recipes, RecipesFavorites, RecipesIngredients,
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

    def create(self, validated_data):
        """Переопределяет метод сохранения данных: для сохранения объекта
        используется метод "create_user()"."""
        user: User = User.objects.create_user(**validated_data)
        return user

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


class RecipesIngredientsSerializer(ModelSerializer):
    """Создает сериализатор для модели "RecipesIngredients"."""

    id = IntegerField(source='ingredient.id')
    name = CharField(source='ingredient.name')
    measurement_unit = CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipesIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_fields(self):
        """Переопределяет поля сериализатора: устанавливает для всех
        параметр "read_only"."""
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields


class RecipesSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes"."""

    author = CustomUserSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(
        many=True,
        source='recipe_ingredient',)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

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

    # ToDo: сделать корректный код
    # def create(self, validated_data):
    #     """Переопределяет метод сохранения данных (POST)."""
    #     validated_data['author'] = self.context['request'].user
    #     ingredients: list = validated_data.get('ingredients', False)
    #     tags: list = validated_data.get('tags', False)
    #     recipe = Recipes.objects.create(**validated_data)
    #     for ingredient in ingredients:
    #         current_ingredient: Ingredients = (
    #             Ingredients.objects.get(id=ingredient['id']))
    #         recipe.recipe_ingredient.set(
    #             amount=ingredient['amount'],
    #             ingredient=current_ingredient)
    #         RecipesIngredients.objects.create(
    #             amount=ingredient['amount'],
    #             recipe=recipe,
    #             ingredient=current_ingredient)
    #     for tag in tags:
    #         current_tag = Tags.objects.get(id=tag)
    #         recipe.recipe_tag.set(
    #             recipe=recipe)
    #     return recipe

    # ToDo: сделать корректный код
    # def update(self, instance, validated_data):
    #     """Переопределяет метод обновления данных (PATCH)."""
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.image = validated_data.get('image', instance.image)
    #     instance.text = validated_data.get('text', instance.text)
    #     instance.cooking_time = validated_data.get(
    #         'cooking_time', instance.cooking_time)
    #     ingredients = validated_data.get('ingredients')
    #     if ingredients:
    #         RecipesIngredients.objects.filter(recipe=instance).delete()
    #         for ingredient in ingredients:
    #             current_ingredient: Ingredients = (
    #                 Ingredients.objects.get(id=ingredient['id']))
    #             RecipesIngredients.objects.create(
    #                 amount=ingredient['amount'],
    #                 recipe=instance,
    #                 ingredient=current_ingredient)
    #     tags = validated_data.get('tags')
    #     if tags:
    #         RecipesTags.objects.filter(recipe=instance).delete()
    #         for tag in tags:
    #             current_tag = Tags.objects.get(id=tag)
    #             RecipesTags.objects.create(recipe=instance, tag=current_tag)
    #     return instance

    def get_is_favorited(self, obj):
        """Показывает наличие рецепта в избранном пользователя в поле
        'is_subscribed'. Возвращает True, если рецепт в избранном,
        False - если нет, или пользователь не авторизован.."""
        user: User = self.context['request'].user
        if user.is_anonymous:
            return False
        return RecipesFavorites.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Показывает наличие рецепта в корзине пользователя в поле
        'is_in_shopping_cart'. Возвращает True, если рецепт в корзине,
        False - если нет, или пользователь не авторизован.."""
        user: User = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCarts.objects.filter(user=user, cart_item=obj).exists()

    def get_fields(self):
        """Определяет сериализатор для поля "tags" в зависимости
        от типа HTTP-запроса."""
        fields = super().get_fields()
        if self.context['request'].method in ('PATCH', 'POST', 'PUT'):
            fields['tags'] = TagsIdListSerializer()
        else:
            fields['tags'] = TagsSerializer(many=True)
        return fields

    # ToDo: проверить необходимость кода:
    # def perform_create(self, serializer):
    #     """Дополняет метод save() для записи в БД:
    #         - добавляет пользователя из запроса в поле "author"."""
    #     serializer.save(author=self.request.user)
    #     return


class RecipesFavoritesSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes" в случае, если происходит
    добавление рецепта в избранное или удаление оттуда."""

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time')

    def create(self, serializer):
        """Дополняет метод save() для записи в БД:
            - добавляет запись в таблицу "RecipesFavorites"."""
        recipe_id = self.kwargs['id']
        recipe: Recipes = get_object_or_404(Recipes, id=recipe_id)
        user: User = self.request.user
        if RecipesFavorites.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка добавления. '
                'Рецепт уже находится в избранном.')
        RecipesFavorites.objects.create(recipe=recipe, user=user)
        return

    def destroy(self, request, *args, **kwargs):
        """Дополняет метод destroy() для удаления из БД:
            - удаляет запись из таблицы "RecipesFavorites"."""
        recipe_id: int = self.kwargs['pk']
        recipe: Recipes = get_object_or_404(Recipes, id=recipe_id)
        user: User = self.request.user
        if not RecipesFavorites.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка удаления. '
                'Рецепта нет в избранном.')
        recipe_favorite: RecipesFavorites = get_object_or_404(
            RecipesFavorites, recipe=recipe_id, user=user)
        recipe_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes" в случае, если происходит
    добавление рецепта в список покупок или удаление оттуда."""

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time')

    def create(self, serializer):
        """Дополняет метод save() для записи в БД:
            - добавляет запись в таблицу "ShoppingCarts"."""
        recipe_id = self.kwargs['id']
        recipe: Recipes = get_object_or_404(Recipes, id=recipe_id)
        user: User = self.request.user
        if ShoppingCarts.objects.filter(
                cart_item=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка добавления. '
                'Рецепт уже находится в корзине.')
        ShoppingCarts.objects.create(recipe=recipe, user=user)
        return

    def destroy(self, request, *args, **kwargs):
        """Дополняет метод destroy() для удаления из БД:
            - удаляет запись из таблицы "ShoppingCarts"."""
        recipe_id: int = self.kwargs['pk']
        recipe: Recipes = get_object_or_404(Recipes, id=recipe_id)
        user: User = self.request.user
        if not ShoppingCarts.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка удаления. '
                'Рецепта нет в корзине.')
        recipe_favorite: ShoppingCarts = get_object_or_404(
            ShoppingCarts, recipe=recipe_id, user=user)
        recipe_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Tags"."""
    class Meta:
        model = Tags
        fields = (
            'id',
            'name',
            'color',
            'slug')


class TagsIdListSerializer(ListField):
    """Создает сериализатор, который принимает список ID тегов.
    Сериализатор используется в RecipesViewSet для HTTP-методов:
        - "PATCH";
        - "POST";
        - "PUT"."""

    child = IntegerField(min_value=1)
