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
    BooleanField, CharField, EmailField, IntegerField, ListField,
    PrimaryKeyRelatedField, SerializerMethodField,
    ValidationError)
from footgram_app.models import (
    Ingredients, Recipes, RecipesFavorites, RecipesIngredients, RecipesTags,
    ShoppingCarts, Subscriptions, Tags)

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


class RecipesSerializerSubscriptions(ModelSerializer):
    """Создает сериализатор для модели "Recipes".
    Содержит в себе краткий перечень полей, необходимый для эндпоинта
    подписок на авторов "/users/subscriptions/".
    Используется в "CustomUserSubscriptionsSerializer". """

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time')


class CustomUserSubscriptionsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Users".
    Содержит в себе расширенный перечень полей, в который включены рецепты,
    необходимый для эндпоинта подписок на авторов "/users/subscriptions/"."""

    recipes = RecipesSerializerSubscriptions(
        source='recipe_author',
        many=True)
    recipes_count = SerializerMethodField()
    """Все объекты модели "User" эндпоинта обязательно являются
    подписками пользователя."""
    is_subscribed = BooleanField(default=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes_count',
            'recipes')

    def get_is_subscribed(self, obj):
        """Передает в поле "is_subscribed" значение "True".
        Все объекты модели "User" эндпоинта обязательно являются
        подписками пользователя."""
        return True

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов у пользователя."""
        return obj.recipe_author.all().count()


class IngredientsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Ingredients"."""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit')


class RecipesIngredientsSerializer(ModelSerializer):
    """Создает сериализатор для поля "ingredients" в "RecipesSerializer"
    для чтения объектов модели "RecipesIngredients" при обработке
    HTTP-методов на чтение:
        - "GET";
        - "LIST"."""

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


class RecipesIngredientsCreateSerializer(ModelSerializer):
    """Создает сериализатор для поля "ingredients" в "RecipesSerializer"
    для создания объектов модели "RecipesIngredients" при обработке
    HTTP-методов на запись:
        - "PATCH";
        - "POST";
        - "PUT"."""

    id = PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    name = SerializerMethodField(read_only=True)
    measurement_unit = SerializerMethodField(read_only=True)

    class Meta():
        model = RecipesIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_name(self, obj):
        """Получает значение поля "name" модели "ingredients"."""
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        """Получает значение поля "measurement_unit" модели "ingredients"."""
        return obj.ingredient.measurement_unit


class RecipesSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes"."""

    author = CustomUserSerializer(read_only=True)
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

    def get_fields(self):
        """Определяет сериализатор для поля "tags" в зависимости
        от типа HTTP-запроса."""
        fields = super().get_fields()
        if self.context['request'].method in ('PATCH', 'POST', 'PUT'):
            fields['ingredients'] = RecipesIngredientsCreateSerializer(
                many=True,
                source='recipe_ingredient')
        else:
            fields['ingredients'] = RecipesIngredientsSerializer(
                many=True,
                source='recipe_ingredient')
        return fields

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
        return ShoppingCarts.objects.filter(user=user, recipe=obj).exists()

    def validate(self, data):
        """Проверяет валидность данных поля "Tags".
        Так как на вход при POST запросе ожидается список целых чисел:
        id (ListField), невозможно осуществить валидацию при помощи
        сериализатора, требуется ручная проверка входящих данных."""
        tags: list[int] = self.context['request'].data.get('tags', None)
        if tags is None:
            if self.context['request'].method == 'PATCH':
                return data
            raise ValidationError({
                "tags": ["Обязательное поле."]})
        bad_ids: list = []
        for tag_id in tags:
            if not Tags.objects.filter(id=tag_id).exists():
                bad_ids.append({
                    'id': [f'Недопустимый первичный ключ "{tag_id}" '
                           '- объект не существует.']})
        if bad_ids:
            raise ValidationError({'tags': bad_ids})
        return data

    def create(self, validated_data):
        """Переопределяет метод сохранения данных (POST)."""
        user: User = self.context['request'].user
        ingredients_data: list[dict] = validated_data.pop('recipe_ingredient')
        current_recipe: Recipes = Recipes.objects.create(
            author=user, **validated_data)
        for ingredient in ingredients_data:
            current_amount: float = ingredient['amount']
            RecipesIngredients.objects.create(
                amount=current_amount,
                ingredient=ingredient['id'],
                recipe=current_recipe)
        tags_data = self.context['request'].data.get('tags')
        current_recipe.tags.set(tags_data)
        return current_recipe

    def update(self, instance, validated_data):
        """Переопределяет метод обновления данных (PATCH)."""
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        RecipesIngredients.objects.filter(recipe=instance).delete()
        ingredients_data: list[dict] = validated_data.pop('recipe_ingredient')
        for ingredient in ingredients_data:
            current_amount: float = ingredient['amount']
            RecipesIngredients.objects.create(
                amount=current_amount,
                ingredient=ingredient['id'],
                recipe=instance)
        tags_data = self.context['request'].data.get('tags')
        RecipesTags.objects.filter(recipe=instance).delete()
        instance.tags.set(tags_data)
        return instance

    def to_representation(self, instance):
        """Переопределяет сериализацию объекта:
            - в поле "tags": сериализатор должен принимать на вход список id
              тегов, а возвращать в ответе полую информацию от объектах;
            - в поле "id: сериализатор должен исключить из выдачи поле 'id',
              при 'PATCH', 'POST' и 'PUT' HTTP-запросах.
            """
        representation = super().to_representation(instance)
        if self.context['request'].method in ('PATCH', 'POST', 'PUT'):
            representation.pop('id')
        tags_data: list = []
        tags: list[Tags] = instance.tags.all()
        for tag in tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'slug': tag.slug})
        representation['tags'] = tags_data
        return representation


class RecipesShortSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes" c ограниченным набором полей
    для отображения в списке покупок."""

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time')


class RecipesFavoritesSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes" в случае, если происходит
    добавление рецепта в избранное или удаление оттуда."""

    class Meta:
        model = RecipesFavorites
        fields = (
            'user',
            'recipe')

    def validate(self, data):
        """Производит валидацию данных:
            - DELETE: проверяет, что пользователь "user" добавил рецепт
              "recipe" в избранное;
            - POST: проверяет, что пользователь "user" не добавляет
              рецепт "recipe" в избранное повторно."""
        user: User = data['user']
        recipe: Recipes = data['recipe']
        request_method: str = self.context['request'].method
        if request_method == 'DELETE' and not RecipesFavorites.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError({
                'recipe':
                    ['Ошибка удаления. Рецепта нет в избранном.']})
        elif request_method == 'POST' and RecipesFavorites.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError({
                'recipe':
                    ['Ошибка добавления. Рецепт уже находится в избранном.']})
        return data

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
    """Создает сериализатор для модели "ShoppingCarts"."""

    class Meta:
        model = ShoppingCarts
        fields = (
            'user',
            'recipe')

    def validate(self, data):
        """Производит валидацию данных:
            - DELETE: проверяет, что пользователь "user" имеет рецепт
              "recipe" в корзине;
            - POST: проверяет, что пользователь "user" не добавляет
              рецепт "recipe" в корзину повторно."""
        user: User = data['user']
        recipe: Recipes = data['recipe']
        request_method: str = self.context['request'].method
        if request_method == 'DELETE' and not ShoppingCarts.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError('Ошибка удаления. Рецепта нет в корзине.')
        elif request_method == 'POST' and ShoppingCarts.objects.filter(
                recipe=recipe, user=user).exists():
            raise ValidationError(
                'Ошибка добавления. Рецепт уже находится в корзине.')
        return data


class SubscriptionsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Subscriptions"."""

    class Meta:
        model = Subscriptions
        fields = (
            'subscriber',
            'subscription_to')

    def validate(self, data):
        """Производит валидацию данных:
            - DELETE:
                - проверяет, что пользователь "subscriber" имеет подписку
                  на пользователя "subscription_to".;
            - POST:
                - проверяет, что пользователь "subscriber" не подписывается
                  сам на себя;
                - проверяет, что пользователь "subscriber" не осуществляет
                  повторную подписку на пользователя "subscription_to"."""
        subscriber: User = data['subscriber']
        subscription_to: User = data['subscription_to']
        request_method: str = self.context['request'].method
        if request_method == 'DELETE' and not Subscriptions.objects.filter(
                subscriber=subscriber,
                subscription_to=subscription_to).exists():
            raise ValidationError(
                "Вы не были подписаны на пользователя "
                f"{subscription_to.username}.")
        elif request_method == 'POST':
            if subscriber.id == subscription_to.id:
                raise ValidationError("Вы не можете подписаться на себя.")
            elif Subscriptions.objects.filter(
                    subscriber=subscriber,
                    subscription_to=subscription_to).exists():
                raise ValidationError(
                    "Вы уже подписаны на пользователя "
                    f"{subscription_to.username}.")
        return data


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
