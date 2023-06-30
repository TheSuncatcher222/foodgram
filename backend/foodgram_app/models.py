"""
Создает модели проекта "Footgram".

Классы-модели:
    - Ingredients
    - Recipes
    - RecipesFavorites
    - RecipesIngredients
    - RecipesTags
    - ShoppingCarts
    - Subscriptions
    - Tags

Создает список используемых в проекте единиц измерения ингредиентов: "UNITS".
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import (
    CASCADE, SET_NULL,
    CharField, FloatField, ForeignKey, ImageField, IntegerField,
    ManyToManyField, SlugField, TextField, UniqueConstraint,
    Model)

INGREDIENTS_NAME_MAX_LENGTH: int = 48
INGREDIENTS_UNIT_MAX_LENGTH: int = 48
TAGS_COLOR_MAX_LEN: int = 7
TAGS_NAME_MAX_LEN: int = 200
TAGS_SLUG_MAX_LEN: int = 200
RECIPES_MEDIA_ROOT: str = 'recipes/images'
RECIPES_NAME_MAX_LEN: int = 128

UNITS: list[tuple[str]] = [
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
    ('ч. л.', 'ч. л.'),
    ('шт.', 'шт.'),
    ('щепотка', 'щепотка')]


class Ingredients(Model):
    """
    Класс для представления ингредиентов.

    Метод __str__ возвращает название ингредиента:
        "Бананы"

    Сортировка производит в алфавитом порядке по возрастанию.

    Атрибуты:
        - name: str
            - уникальное название ингредиента
            - установлено ограничение по длине
            - установлено ограничение по уникальности
            - индексируется
        - measurement_unit: str
            - единица измерения ингредиента
            - установлено ограничение по длине
            - установлено ограничение выбора значения согласно списку "UNITS"
    """
    name = CharField(
        db_index=True,
        max_length=INGREDIENTS_NAME_MAX_LENGTH,
        verbose_name='Название')
    measurement_unit = CharField(
        choices=UNITS,
        max_length=INGREDIENTS_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='name_with_unit')]
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        self.full_clean()
        super().save(*args, **kwargs)


class Tags(Model):
    """
    Класс для представления тегов.

    Метод __str__ возвращает название и слаг тега:
        "Вкусно (vkusno)"

    Сортировка производит в алфавитом порядке по возрастанию.

    Атрибуты:
        - color: str
            - уникальное значение цвета тега в формате HEX (#RRGGBB)

        - name: str
            - уникальное название тега
            - установлено ограничение по длине
            - установлено ограничение по уникальности
            - индексируется
        slug: str
            уникальное значение для формирование URL тега

    Индексируемые атрибуты:
        name

    Модель позволяет указывать HEX коды в упрощенном состоянии (#RGB) и
    при сохранении приводит их в полной форме (#RRGGBB) при помощи функции
    "_validate_hex_format".
    """
    color = CharField(
        max_length=TAGS_COLOR_MAX_LEN,
        validators=[RegexValidator(
            regex=r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$',
            message='Введите корректный HEX цвет!')],
        unique=True,
        verbose_name='HEX цвет')
    name = CharField(
        db_index=True,
        max_length=TAGS_NAME_MAX_LEN,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[А-ЯЁ]{1}[а-яё]*$',
            message=(
                'Введите корректное название тега '
                '(одно слово с заглавной буквы!'))],
        verbose_name='Название')
    slug = SlugField(
        max_length=TAGS_SLUG_MAX_LEN,
        unique=True,
        verbose_name='Краткий URL')

    class Meta:
        ordering = ('name', )
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name} ({self.slug})'

    def _validate_hex_format(self) -> str:
        """Производит валидацию значения цветового HEX кода: приводит его к
        формату #RRGGBB. Возвращает 6-значный цветовой код."""
        if self.color and len(self.color) == 4:
            self.color = (
                f'#{self.color[1]*2}{self.color[2]*2}{self.color[3]*2}')
        return

    def save(self, *args, **kwargs):
        """Переопределяет метод сохранения модели:
            - производит дополнительную валидацию поля "color";
            - вызывает метод full_clean()."""
        self._validate_hex_format()
        self.full_clean()
        super().save(*args, **kwargs)


class Recipes(Model):
    """
    Класс для представления рецептов.

    Метод __str__ возвращает название и время приготовления рецепта (в мин):
        "Лазанья (120 мин.)"

    Сортировка производится по дате публикации от новых к старым.

    Атрибуты:
        - author: int
            - ID автора рецепта
            - связь через ForeignKey к модели "User"
            - при удалении пользователя удаляются все рецепты
        - cooking_time: int
            - время приготовления рецепта (в минутах)
            - установлено ограничение по значению: не менее 1
        - image: str
            - картинка рецепта (Base64)
        - ingredients:
            - список ингредиентов
            - связь через ManyToManyField и таблицу "RecipesIngredients"
        - name: str
            - уникальное название рецепта
            - установлено ограничение по длине
            - установлено ограничение по уникальности
            - индексируется
        - tags:
            - список тегов
            - связь через ManyToManyField и таблицу "RecipesTags"
        - text: str
            - текстовое описание рецепта
    """
    author = ForeignKey(
        on_delete=CASCADE,
        related_name='recipe_author',
        to=User,
        verbose_name='Автор')
    cooking_time = IntegerField(
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Время должно составлять не менее 1 минуты!')],
        verbose_name='Время приготовления (мин.)')
    image = ImageField(
        upload_to=RECIPES_MEDIA_ROOT,
        verbose_name='Картинка рецепта')
    ingredients = ManyToManyField(
        through='RecipesIngredients',
        to=Ingredients,
        verbose_name='Ингредиенты')
    name = CharField(
        db_index=True,
        max_length=RECIPES_NAME_MAX_LEN,
        unique=True,
        verbose_name='Название')
    tags = ManyToManyField(
        related_name='recipes',
        to=Tags,
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RecipesFavorites(Model):
    """
    Класс для представления избранных рецептов.

    Связывает таблицы "Recipes" и "Users".

    Метод __str__ возвращает информацию по избранному рецепту:
        Пользователь Omnomnom777 добавил рецепт "Лазанья" в избранное

    Сортировка производится по дате добавления по убыванию от новых к старым.

    Атрибуты:
        - user: int
            - ID пользователя
            - связь через ForeignKey к модели "User"
        - recipe: int
            - ID рецепта
            - связь через ForeignKey к модели "Recipes"

    Атрибуты проходят проверку на уникальное сочетание.
    """
    user = ForeignKey(
        on_delete=CASCADE,
        related_name='user_recipe_favorite',
        to=User,
        verbose_name='Пользователь')
    recipe = ForeignKey(
        on_delete=CASCADE,
        related_name='recipe_favorite_user',
        to=Recipes,
        verbose_name='Рецепт')

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
            f'{self.user.username}: "{self.recipe}"')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RecipesIngredients(Model):
    """
    Класс для предоставления ингредиентов рецепта.

    Связывает таблицы "Ingredients" и "Recipes".

    Метод "__str__" возвращает информацию по рецепте и ингредиенте:
        "Лазанья - Сыр"

    Сортировка производится по названию рецепта и названию ингредиента
    по возрастанию.

    Атрибуты:
        - ingredient: int
            - ID ингредиента
            - связь через ForeignKey к модели "Ingredients"
        - recipe: int
            - ID рецепта
            - связь через ForeignKey к модели "Recipes"

    Атрибуты проходят проверку на уникальное сочетание.
    """
    amount = FloatField(
        validators=[
            MinValueValidator(
                limit_value=0.01,
                message='Укажите количество ингредиента!')],
        verbose_name='Количество')
    ingredient = ForeignKey(
        on_delete=CASCADE,
        related_name='ingredient_recipe',
        to=Ingredients,
        verbose_name='Ингредиент')
    recipe = ForeignKey(
        on_delete=CASCADE,
        related_name='recipe_ingredient',
        to=Recipes,
        verbose_name='Рецепт')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='recipe_ingredient')]
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Связь моделей "Рецепты" и "Ингредиенты"'
        verbose_name_plural = 'Связи моделей "Рецепты" и "Ингредиенты"'

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RecipesTags(Model):
    """
    Класс для предоставления тегов рецептов.

    Связывает таблицы 'Recipes' и 'Tags'.

    Метод __str__ возвращает информацию по рецепте и теге:
        Лазанья - Вкусно

    Сортировка производится по названию рецепта и названию тега по возрастанию.

    Атрибуты:
        - recipe: int
            - ID рецепта
            - связь через ForeignKey к модели "Recipes"
        - tag: int
            - ID тега
            - связь через ForeignKey к модели "Tags"

    Атрибуты проходят проверку на уникальное сочетание.
    """
    recipe = ForeignKey(
        null=True,
        on_delete=SET_NULL,
        related_name='recipe_tag',
        to=Recipes,
        verbose_name='Рецепт')
    tag = ForeignKey(
        null=True,
        on_delete=SET_NULL,
        related_name='tag_recipe',
        to=Tags,
        verbose_name='Тег')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipe_tag')]
        ordering = ('recipe', 'tag')
        verbose_name = 'Связь моделей "Рецепты" и "Теги"'
        verbose_name_plural = 'Связи моделей "Рецепты" и "Теги"'

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ShoppingCarts(Model):
    """
    Класс для представления списка покупок.

    Связывает таблицы "User" и "Recipes".

    Метод __str__ возвращает название рецепта в корзине пользователя:
        "Рецепт "Лазанья" в корзине пользователя Omnomnom777"

    Сортировка производится по пользователю и рецепту по возрастанию.

    Атрибуты:
        - user: int
            - ID пользователя
            - связь через ForeignKey к модели "User"
        - recipe: int
            - ID рецепта, добавленный в корзину
            - связь через ForeignKey к модели "Recipes"
    """
    user = ForeignKey(
        on_delete=CASCADE,
        related_name='shopping_cart',
        to=User,
        verbose_name='Корзина пользователя')
    recipe = ForeignKey(
        null=True,
        on_delete=SET_NULL,
        to=Recipes,
        related_name='shopping_cart',
        verbose_name='Рецепт в корзине')

    class Meta:
        ordering = ('user', 'recipe')
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return (
            f'{self.user.username}: "{self.recipe}"')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Subscriptions(Model):
    """
    Класс для представления подписок пользователей друг на друга.

    Метод __str__ возвращает значение подписки:
        "Подписка Omnomnom777 на Amnyamnyam999"

    Сортировка производится по дате подписки по убыванию от новых к старым.

    Атрибуты:
        - subscriber: int
            - ID пользователя, осуществляющего подписку
            - связь через ForeignKey к модели "User"
        - subscription_to: int
            - ID пользователя, на которого осуществляется подписка
            - связь через ForeignKey к модели "User"

    Проверяет уникальность подписки одного пользователя на другого.
    Допускает взаимные подписки.
    """
    subscriber = ForeignKey(
        on_delete=CASCADE,
        related_name='subscriber',
        to=User,
        verbose_name='Подписчик')
    subscription_to = ForeignKey(
        on_delete=CASCADE,
        related_name='subscription_author',
        to=User,
        verbose_name='Автор на которого подписка')

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки на авторов'

    def __str__(self):
        return (
            f'Подписка {self.subscriber.username} '
            f'на {self.subscription_to.username}')

    @staticmethod
    def _validate_unique_subscription(self):
        """Проверяет уникальность подписки user_1 на user_2."""
        if Subscriptions.objects.filter(
                subscriber=self.subscriber,
                subscription_to=self.subscription_to).exists():
            raise ValidationError(
                'Подписка между данными пользователями уже существует!')
        return

    def save(self, *args, **kwargs):
        self.full_clean()
        self._validate_unique_subscription(self)
        super().save(*args, **kwargs)
