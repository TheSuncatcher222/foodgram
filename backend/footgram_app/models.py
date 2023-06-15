"""
Создает модели проекта "Footgram".

Классы-модели:
    - Ingredients
    - Recipes
    - RecipesFavoritesUsers
    - RecipesIngredients
    - RecipesTags
    - ShoppingCarts
    - Subscriptions
    - Tags

Создает список используемых в проекте единиц измерения: "UNITS".
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import (
    CASCADE,
    CharField, ForeignKey, ImageField, IntegerField, ManyToManyField,
    SlugField, TextField, UniqueConstraint,
    Model)

UNITS = [
    ('банка', 'банка'),
    ('батон', 'батон'),
    ('бутылка', 'бутылка'),
    ('г', 'г'),
    ('горсть', 'горсть'),
    ('долька', 'долька'),
    ('звездочка', 'звездочка'),
    ('зубчик', 'зубчик'),
    ('капля', 'капля'),
    ('кусок', 'кусок'),
    ('л', 'л'),
    ('лист', 'лист'),
    ('мл', 'мл'),
    ('пакет', 'пакет'),
    ('пакетик', 'пакетик'),
    ('пачка', 'пачка'),
    ('пласт', 'пласт'),
    ('по вкусу', 'по вкусу'),
    ('пучок', 'пучок'),
    ('ст. л.', 'ст. л.'),
    ('стакан', 'стакан'),
    ('стебель', 'стебель'),
    ('стручок', 'стручок'),
    ('тушка', 'тушка'),
    ('упаковка', 'упаковка'),
    ('щепотка', 'щепотка'),
    ('шт.', 'шт.'),
    ('ч. л.', 'ч. л.')
]


class Ingredients(Model):
    """
    Класс для представления ингридиентов.

    Метод __str__ возвращает название ингридиента:
        "Бананы"

    Сортировка производит в алфавитом порядке по возрастанию.

    Атрибуты
        name: str
            уникальное название ингридиента
        measurement_unit: str
            единица измерения ингридиента
            (должна содержаться в установленном списке единиц "UNITS")

    Индексируемые атрибуты:
        name
    """
    name = CharField(
        db_index=True,
        max_length=48,
        verbose_name='Название',
        unique=True)
    measurement_unit = CharField(
        choices=UNITS,
        max_length=48,
        verbose_name='единица измерения')

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}'


class Tags(Model):
    """
    Класс для представления тегов.

    Метод __str__ возвращает название и слаг тега:
        "Вкусно (vkusno)"

    Сортировка производит в алфавитом порядке по возрастанию (АБВ).

    Атрибуты
        name: str
            уникальное название тега
        color: str
            уникальное значение цвета тега в формате HEX (#RGB или #RRGGBB)
        slug: str
            уникальное значение для формирование URL тега

    Индексируемые атрибуты:
        name
    """
    name = CharField(
        db_index=True,
        max_length=32,
        verbose_name='Название')
    color = CharField(
        max_length=7,
        validators=[RegexValidator(
            regex=r'^(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})$',
            message='Enter a valid HEX code (e.g. #RRGGBB or #RGB)!')],
        unique=True,
        verbose_name='HEX цвет')
    slug = SlugField(
        unique=True,
        verbose_name='Краткий URL')

    class Meta:
        ordering = ('name', )
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name} ({self.slug})'


class Recipes(Model):
    """
    Класс для представления рецептов.

    Метод __str__ возвращает название и время приготовления рецепта (в мин):
        "Лазанья (120 мин.)"

    Сортировка производится по дате публикации от новых к старым.

    Атрибуты
        author: int
            ID автора рецепта
            связь через ForeignKey к модели "User"
        cooking_time: int
            время приготовления рецепта (в минутах)
        image: str
            картинка рецепта (Base64)
        ingredients:
            список ингридиентов
            связь через ManyToManyField и таблицу 'RecipesIngredients'
        name: str
            уникальное название рецепта
        tags:
            список тегов
            связь через ManyToManyField и таблицу 'RecipesTags'
        text: str
            текстовое описание рецепта

    Индексируемые атрибуты:
        name
    """
    author = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='recipe_author',
        verbose_name='Автор')
    cooking_time = IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (в минутах)')
    image = ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка рецепта')
    ingredients = ManyToManyField(
        Ingredients,
        through='RecipesIngredients',
        verbose_name='Ингридиенты')
    name = CharField(
        db_index=True,
        max_length=128,
        unique=True,
        verbose_name='Название')
    tags = ManyToManyField(
        Tags,
        through='RecipesTags',
        verbose_name='Теги')
    text = TextField(
        verbose_name='Описание')

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name} ({self.cooking_time} мин.)'


class ShoppingCarts(Model):
    """
    Класс для представления списка покупок.

    Связывает таблицы "User" и "Recipes".

    Метод __str__ возвращает название рецепта в корзине пользователя:
        "Рецепт "Лазанья" в корзине пользователя Omnomnom777"

    Сортировка производится по пользователю и рецепту по возрастанию.

    Атрибуты
        user: int
            ID пользователя
            связь через ForeignKey к модели "User"
        cart_item: int
            ID рецепта, добавленный в корзину
            связь через ForeignKey к модели "Recipes"
    """
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='shopping_cart',
        verbose_name='Корзина пользователя')
    cart_item = ForeignKey(
        Recipes,
        on_delete=CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт в корзине')

    class Meta:
        ordering = ('user', 'cart_item')
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return (
            f'Рецепт "{self.cart_item}" в корзине '
            f'пользователя {self.user.username}')


class Subscriptions(Model):
    """
    Класс для представления подписок пользователей друг на друга.

    Метод __str__ возвращает значение подписки:
        "Подписка Omnomnom777 на Amnyamnyam999"

    Сортировка производится по дате подписки по убыванию от новых к старым.

    Атрибуты
        subscriber: int
            ID пользователя, осуществляющего подписку
            связь через ForeignKey к модели "User"
        subscription_to: int
            ID пользователя, на которого осуществляется подписка
            связь через ForeignKey к модели "User"
    """
    subscriber = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='subscriber',
        verbose_name='подписчик')
    subscription_to = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='subscription_author',
        verbose_name='автор на которого подписка')

    class Meta:
        # Проверка на UniqueConstraint не может быть произведена,
        # так как подписки должны работать в обе стороны.
        # Функционал реализован в сериализаторе SubscriptionsSerializer.
        ordering = ('-id', )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (
            f'Подписка {self.subscriber.username} '
            f'на {self.subscription_to.username}')


class RecipesFavoritesUsers(Model):
    """
    Класс для представления избранных рецептов.

    Связывает таблицы 'Recipes' и 'Users'.

    Метод __str__ возвращает информацию по избранному рецепту:
        Пользователь Omnomnom777 добавил рецепт "Лазанья" в избранное

    Сортировка производится по дате добавления по убыванию от новых к старым.

    Атрибуты
        user: int
            ID пользователя
            связь через ForeignKey к модели "User"
        recipe: int
            ID рецепта
            связь через ForeignKey к модели "Recipes"
    """
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='user_recipe_favorite',
        verbose_name='ID пользователя')
    recipe = ForeignKey(
        Recipes,
        on_delete=CASCADE,
        related_name='recipe_favorite_user',
        verbose_name='ID рецепта')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_favorite_recipe')]
        ordering = ('-id',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return (
            f'Пользователь {self.user.username} добавил '
            f'рецепт "{self.recipe.name}" в избранное')


class RecipesIngredients(Model):
    """
    Класс для предоставления ингридиентов рецепта.

    Связывает таблицы 'Ingredients' и 'Recipes'.

    Метод __str__ возвращает информацию по рецепте и ингридиенте:
        Лазанья - Сыр

    Сортировка производится по названию рецепта и названию ингридиента
    по возрастанию.

    Атрибуты
        ingredient: int
            ID ингридиента
            связь через ForeignKey к модели "Ingredients"
        recipe: int
            ID рецепта
            связь через ForeignKey к модели "Recipes"
    """
    ingredient = ForeignKey(
        Ingredients,
        on_delete=CASCADE,
        related_name='ingredient_recipe',
        verbose_name='ID ингридиента')
    recipe = ForeignKey(
        Recipes,
        on_delete=CASCADE,
        related_name='recipe_ingredient',
        verbose_name='ID рецепта')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='recipe_ingredient')]
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Связь моделей \'Рецепты\' и \'Ингридиенты\''
        verbose_name_plural = 'Связи моделей \'Рецепты\' и \'Ингридиенты\''

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class RecipesTags(Model):
    """
    Класс для предоставления тегов рецептов.

    Связывает таблицы 'Recipes' и 'Tags'.

    Метод __str__ возвращает информацию по рецепте и теге:
        Лазанья - Вкусно

    Сортировка производится по названию рецепта и названию тега по возрастанию.

    Атрибуты
        recipe: int
            ID рецепта
            связь через ForeignKey к модели "Recipes"
        tag: int
            ID тега
            связь через ForeignKey к модели "Tags"
    """
    recipe = ForeignKey(
        Recipes,
        on_delete=CASCADE,
        related_name='recipe_tag',
        verbose_name='ID рецепта')
    tag = ForeignKey(
        Tags,
        on_delete=CASCADE,
        related_name='tag_recipe',
        verbose_name='ID тега')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipe_tag')]
        ordering = ('recipe', 'tag')
        verbose_name = 'Связь моделей \'Рецепты\' и \'Теги\''
        verbose_name_plural = 'Связи моделей \'Рецепты\' и \'Теги\''

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'
