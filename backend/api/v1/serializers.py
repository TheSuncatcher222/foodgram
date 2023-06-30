"""
Создает сериализаторы моделей проекта "Foodgram".

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
import base64
import inspect

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from re import sub, search
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.serializers import (
    Serializer, ModelSerializer,
    BooleanField, CharField, EmailField, ImageField, IntegerField, ListField,
    PrimaryKeyRelatedField, SerializerMethodField,
    ValidationError)
from foodgram_app.models import (
    Ingredients, Recipes, RecipesFavorites, RecipesIngredients, RecipesTags,
    ShoppingCarts, Subscriptions, Tags)

USER_EMAIL_MAX_LEN: int = 254
USER_FIRST_NAME_MAX_LEN: int = 150
USER_PASSWORD_MAX_LEN: int = 150
USER_SECOND_NAME_MAX_LEN: int = 150
USER_USERNAME_MAX_LEN: int = 150

USER_FORBIDDEN_USERNAMES: list[str] = ['me']

USERNAME_PATTERN: str = r'^[\w.@+-]+$'


class APICustomException(APIException):
    """Возвращает ошибку 500 с указанием того, что ошибка на сервере.
    Для упрощения дебага указывает имя файла и номер строки, где была
    вызвана ошибка. Для безопасности имя файла засекречивается:
    берется только его первая буква."""

    def __init__(self):
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        filename = search(r'(\w+\.py)', frame.f_code.co_filename).group(1)[0]
        self.detail = f"'Internal Server Error. Mark <{filename}.{lineno}>"
        self.code = status.HTTP_500_INTERNAL_SERVER_ERROR


class Base64ImageField(ImageField):
    """Сериализатор изображений в формате base64."""
    def to_internal_value(self, data):
        """Декодирует данные, если было прислано изображение в формате
        base64.
        Структура имеет следующий вид:
            - "data:[<MIME-type>][;base64],<data>";
            - "data:image/png;base64,iVBORw0KGg..."."""
        if isinstance(data, str) and data.startswith('data:image'):
            data_format, base64_image = data.split(';base64,')
            image_extension: str = data_format.split('/')[-1]
            data: ContentFile = ContentFile(
                base64.b64decode(base64_image),
                name='image.' + image_extension)
        return super().to_internal_value(data)


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
        request = self.context.get('request', None)
        if not request:
            raise APICustomException()
        user: User = request.user
        return not user.is_anonymous and user.subscriber.filter(
            subscription_to=obj).exists()

    def validate_email(self, value):
        """Производит валидацию поля 'email' проверяет на уникальность.
        Проверка необходима, так как непереопределенная модель User пропускает
        разных пользователей с одной почтой.
        """
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
            sort_chars: str = ' '.join(
                f'{c}' for c in sorted(set(forbidden_chars)))
            raise ValidationError(
                f'Использование [{sort_chars}] в имени '
                'пользователя запрещено.')
        for forbidden in USER_FORBIDDEN_USERNAMES:
            if value.lower() == forbidden.lower():
                raise ValidationError(
                    f'Пользователь с именем "{forbidden}" недопустим.')
        if User.objects.filter(username=value).exists():
            raise ValidationError(
                'Пользователь с таким именем уже существует.')
        return value


class CustomUserLoginSerializer(Serializer):
    """Создает сериализатор для валидации аунтификационных данных на
    URL ".../auth/token/login/"."""
    
    email = EmailField()
    password = CharField()

    def validate(self, data):
        """Проверяет корректность указанных полей:
            - email;
            - password.
        Возвращает объект пользователя в случае успешной аутентификации."""
        request = self.context.get('request', None)
        if not request:
            raise APICustomException()
        email: str = data.get('email', None)
        password: str = data.get('password', None)
        if email is None or password is None:
            raise ValidationError('Не указана электронная почта или пароль!')
        if not User.objects.filter(email=email).exists():
            raise ValidationError(
                'Указана неверная электронная почта или пароль!')
        username: str = User.objects.get(email=email).username
        user = authenticate(
            request=request,
            username=username,
            password=password)
        if not user:
            raise ValidationError(
                'Указана неверная электронная почта или пароль!')
        data['user'] = user
        return data


class RecipesShortSerializer(ModelSerializer):
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

    recipes = RecipesShortSerializer(
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

    def to_representation(self, instance):
        """Получает из запроса значение """
        representation = super().to_representation(instance)
        if representation.get('recipes', None) is None:
            raise APICustomException()
        recipes_limit: None = None
        request = self.context.get('request', None)
        if request is not None:
            recipes_limit: str = request.query_params.get(
                'recipes_limit', None)
        if recipes_limit is not None:
            representation['recipes'] = representation[
                'recipes'][:int(recipes_limit)]
        return representation


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
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount')

    # ToDo: выглядит громоздко, исправить на read_only_fields, протестировать
    def get_fields(self):
        """Переопределяет поля сериализатора: устанавливает для всех
        параметр "read_only"."""
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields


# ToDo: попробовать убрать сериализатор.
class RecipesIngredientsCreateSerializer(ModelSerializer):
    """Создает сериализатор для поля "ingredients" в "RecipesSerializer"
    для создания объектов модели "RecipesIngredients" при обработке
    HTTP-методов на запись:
        - "PATCH";
        - "POST";
        - "PUT"."""

    id = PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    measurement_unit = SerializerMethodField(read_only=True)
    name = SerializerMethodField(read_only=True)

    class Meta():
        model = RecipesIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount')

    def get_measurement_unit(self, obj):
        """Получает значение поля "measurement_unit" модели "ingredients"."""
        return obj.ingredient.measurement_unit
    
    def get_name(self, obj):
        """Получает значение поля "name" модели "ingredients"."""
        return obj.ingredient.name


class RecipesSerializer(ModelSerializer):
    """Создает сериализатор для модели "Recipes"."""

    author = CustomUserSerializer(read_only=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

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

    # ToDo: create и update очень похожи, можно вынести одинаковый код
    def create(self, validated_data):
        """Переопределяет метод сохранения данных (POST)."""
        request = self.context.get('request', None)
        if not request:
            raise APICustomException()
        user: User = request.user
        """Не нужно проверять наличие полей в validated_data и context
        так как это уде проверяется в методе validate."""
        ingredients_data: list[dict] = validated_data.pop('recipe_ingredient')
        current_recipe: Recipes = Recipes.objects.create(
            author=user, **validated_data)
        recipe_ingredients: list = []
        for ingredient in ingredients_data:
            current_amount: float = ingredient['amount']
            recipe_ingredients.append(RecipesIngredients(
                amount=current_amount,
                ingredient=ingredient['id'],
                recipe=current_recipe))
        RecipesIngredients.objects.bulk_create(recipe_ingredients)
        tags_data = self.context['request'].data.get('tags')
        current_recipe.tags.set(tags_data)
        return current_recipe

    def get_fields(self):
        """Определяет сериализатор для поля "tags" в зависимости
        от типа HTTP-запроса."""
        fields = super().get_fields()
        request = self.context.get('request', None)
        if fields.get('ingredients', None) is None:
            raise APICustomException()
        if request is not None and request.method in ('PATCH', 'POST', 'PUT'):
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
        return self._get_is_check(obj_queryset=obj.recipe_favorite_user)

    def get_is_in_shopping_cart(self, obj):
        """Показывает наличие рецепта в корзине пользователя в поле
        'is_in_shopping_cart'. Возвращает True, если рецепт в корзине,
        False - если нет, или пользователь не авторизован.."""
        return self._get_is_check(obj_queryset=obj.shopping_cart)

    def to_representation(self, instance):
        """Переопределяет сериализацию объекта:
            - в поле "tags": сериализатор должен принимать на вход список id
              тегов, а возвращать в ответе полую информацию от объектах;
            - в поле "id: сериализатор должен исключить из выдачи поле 'id',
              при 'PATCH', 'POST' и 'PUT' HTTP-запросах.
            """
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        if not request or 'id' not in representation:
            raise APICustomException()
        if request.method in ('PATCH', 'POST', 'PUT'):
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
        ingredients_data: list = []
        recipe_ingredients = instance.recipe_ingredient.all()
        for recipe_ingredient in recipe_ingredients:
            ingredient = recipe_ingredient.ingredient
            ingredients_data.append({
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': recipe_ingredient.amount})
        representation['ingredients'] = ingredients_data
        return representation

    def update(self, instance, validated_data):
        """Переопределяет метод обновления данных (PATCH)."""
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        RecipesIngredients.objects.filter(recipe=instance).delete()
        """Не нужно проверять наличие полей в validated_data и context
        так как это уде проверяется в методе validate."""
        ingredients_data: list[dict] = validated_data.pop('recipe_ingredient')
        recipe_ingredients: list = []
        for ingredient in ingredients_data:
            current_amount: float = ingredient['amount']
            recipe_ingredients.append(RecipesIngredients(
                amount=current_amount,
                ingredient=ingredient['id'],
                recipe=instance))
        RecipesIngredients.objects.bulk_create(recipe_ingredients)
        tags_data = self.context['request'].data.get('tags')
        RecipesTags.objects.filter(recipe=instance).delete()
        instance.tags.set(tags_data)
        instance.save()
        return instance

    def validate(self, data):
        """Проверяет валидность данных поля "Tags".
        Так как на вход при POST запросе ожидается список целых чисел:
        id (ListField), невозможно осуществить валидацию при помощи
        сериализатора, требуется ручная проверка входящих данных."""
        ingredients = data.get('recipe_ingredient', None)
        self._validate_ingredients(ingredients=ingredients)
        tags: list[int] = self.context['request'].data.get('tags', None)
        self._validate_tags(tags=tags)
        """При PATCH запросе (кнопка "редактировать") фронт получает
        изображение рецепта (instance.image), но при отправке запроса
        изображение не прикрепляется."""
        image: str = data.get('image', None)
        if self.context['request'].method != 'PATCH':
            self._validate_image(image=image)
        return data

    def _get_is_check(self, obj_queryset):
        """Вспомогательная функция:
            - проверяет авторизован ли пользователь;
            - проверяет существует ли в сообщенном queryset хотя бы
              один объект с фильтрацией по user."""
        request = self.context.get('request', None)
        if request is None:
            raise APICustomException()
        user: User = request.user
        return (
            not user.is_anonymous and
            obj_queryset.filter(user=user).exists())

    def _validate_ingredients(self, ingredients: list) -> None:
        """Вспомогательная функция для "validate": производит валидацию
        ингредиентов из списка присланных."""
        for ingredient in ingredients:
            if 'id' not in ingredient:
                raise ValidationError(
                    {'ingredients': {'id': ["Обязательное поле."]}})
            if 'amount' not in ingredient:
                raise ValidationError(
                    {'ingredients': {'amount': ["Обязательное поле."]}})
            if not isinstance(ingredient['amount'], float):
                raise ValidationError(
                    {'ingredients': {'amount': [
                        'Недопустимый формат ввода! '
                        'Укажите количество ингредиента.']}})
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError('В рецепте продублированы ингредиенты!')
        return

    def _validate_image(self, image: str) -> None:
        """Вспомогательная функция для "validate": производит валидацию
        изображения рецепта."""
        if image is None:
            raise ValidationError({
                "image": ["Файл не был прикреплен."]})
        return

    def _validate_tags(self, tags: list) -> None:
        """Вспомогательная функция для "validate": производит валидацию
        тегов из списка присланных."""
        self._validate_field_required(name='tags', value=tags)
        if not isinstance(tags, list):
            raise ValidationError({
                "tags": ["Укажите ID в формате списка."]})
        if len(tags) == 0:
            raise ValidationError({
                "tags": ["Поле не может быть пустым."]})
        bad_ids: list = []
        for tag_id in tags:
            if not isinstance(tag_id, int):
                bad_ids.append({
                    'id': ['Недопустимый формат ввода! '
                           'Укажите список ID тегов.']})
            elif not Tags.objects.filter(id=tag_id).exists():
                bad_ids.append({
                    'id': [f'Недопустимый первичный ключ "{tag_id}" '
                           '- объект не существует.']})
        if bad_ids:
            raise ValidationError({'tags': bad_ids})
        return


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
        request = self.context.get('request', None)
        if not request:
            raise APICustomException()
        request_method: str = request.method
        user: User = data.get('user', None)
        recipe: Recipes = data.get('recipe', None)
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
        recipe_id = self.kwargs.get('id', None)
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
        recipe_id = self.kwargs.get('id', None)
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
        request = self.context.get('request', None)
        if not request:
            raise APICustomException()
        request_method: str = request.method
        user: User = data['user']
        recipe: Recipes = data['recipe']
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
        request = self.context.get('request', None)
        if not request:
            raise APICustomException()
        request_method: str = request.method
        subscriber: User = data['subscriber']
        subscription_to: User = data['subscription_to']
        subscription_exists: bool = Subscriptions.objects.filter(
                subscriber=subscriber,
                subscription_to=subscription_to).exists()
        if request_method == 'DELETE' and not subscription_exists:
            raise ValidationError(
                "Вы не были подписаны на пользователя "
                f"{subscription_to.username}.")
        elif request_method == 'POST':
            if subscriber.id == subscription_to.id:
                raise ValidationError("Вы не можете подписаться на себя.")
            elif subscription_exists:
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
