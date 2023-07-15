import os

import pytest
import shutil
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import CASCADE, SET_NULL

from foodgram_app.models import (
    Ingredients, Recipes, RecipesFavorites, RecipesIngredients,
    RecipesTags, ShoppingCarts, Subscriptions, Tags)

IMAGE_BYTES: bytes = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B')
IMAGE_TEST_FOLDER: str = 'test_media'

TEST_OBJECTS_COUNT: int = 2


def create_ingredient_obj(num: int) -> Ingredients:
    """Создает и возвращает объект модели "Ingredients"."""
    return Ingredients.objects.create(
        name=f'test_ingredient_name_{num}',
        measurement_unit='батон')


def create_recipe_ingredient_obj(
        amount: float,
        ingredient: Ingredients,
        recipe: Recipes) -> RecipesIngredients:
    """Создает и возвращает объект модели "RecipesIngredients"."""
    return RecipesIngredients.objects.create(
        amount=amount,
        ingredient=ingredient,
        recipe=recipe)


def create_recipe_obj(num: int, user: User) -> None:
    """Создает и возвращает объект модели "Recipes".
    Изображения сохраняются в отдельную субдиректорию медиа для тестов."""
    image_file: ContentFile = ContentFile(IMAGE_BYTES)
    uploaded_image: SimpleUploadedFile = SimpleUploadedFile(
        f'test_image_{num}.gif', image_file.read(), content_type='image/gif')
    recipe: Recipes = Recipes.objects.create(
        author=user,
        cooking_time=num,
        image=uploaded_image,
        name=f'test_recipe_name_{num}',
        text=f'test_recipe_text_{num}')
    return recipe


def create_recipe_tag_obj(recipe: Recipes, tag: Tags) -> RecipesTags:
    """Создает и возвращает объект модели "RecipesTags"."""
    return RecipesTags.objects.create(
        recipe=recipe,
        tag=tag)


def create_recipe_favorite_obj(
        recipe: Recipes, user: User) -> RecipesFavorites:
    """Создает и возвращает объект модели "Ingredients"."""
    return RecipesFavorites.objects.create(
        recipe=recipe,
        user=user)


def create_shopping_cart_obj(recipe: Recipes, user: User) -> ShoppingCarts:
    """Создает и возвращает объект модели "ShoppingCarts"."""
    return ShoppingCarts.objects.create(
        user=user,
        recipe=recipe)


def create_subscription_obj(
        subscriber: User, subscription_to: User) -> Subscriptions:
    """Создает и возвращает объект модели "Subscriptions"."""
    return Subscriptions.objects.create(
        subscriber=subscriber,
        subscription_to=subscription_to)


def create_tag_obj(num: int, unique_color: str = 'NoData') -> Tags:
    """Создает и возвращает объект модели "Tags"."""
    if unique_color == 'NoData':
        color: str = f"#{'0'*(6-len(str(num)))}{num}"
    else:
        color: str = unique_color
    return Tags.objects.create(
        color=color,
        name=f"Те{'г'*num}",
        slug=f'test_tag_slug_{num}')


def create_user_obj(num: int) -> User:
    """Создает и возвращает объект модели "User".
    Высокое быстродействие за счет отсутствия шифрования пароля.
    Тесты, которые требуют валидации поля "password" будут провалены!"""
    return User.objects.create(
        email=f'test_user_email_{num}@email.com',
        username=f'test_user_username_{num}',
        first_name=f'test_user_first_name_{num}',
        last_name=f'test_user_last_name_{num}',
        password=f'test_user_password_{num}')


def create_user_obj_with_hash(num: int) -> User:
    """Создает и возвращает объект модели "User".
    Низкое быстродействие за счет шифрования пароля.
    Следует применять в тестах, которые требуют валидации поля "password"."""
    return User.objects.create_user(
        email=f'test_user_email_{num}@email.com',
        username=f'test_user_username_{num}',
        first_name=f'test_user_first_name_{num}',
        last_name=f'test_user_last_name_{num}',
        password=f'test_user_password_{num}')


@pytest.mark.django_db
class TestIngredientsModel():
    """Производит тест модели "Ingredients"."""

    INGREDIENTS_VALID_UNITS: dict = [
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
        ('ч. л.', 'ч. л.')]

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        assert Ingredients.objects.all().count() == 0
        ingredient: Ingredients = create_ingredient_obj(num=1)
        assert Ingredients.objects.all().count() == 1
        assert ingredient.name == 'test_ingredient_name_1'
        assert ingredient.measurement_unit == 'батон'
        return

    def test_valid_choices(self) -> None:
        """Тестирует список выбора choices поля "measurement_unit":
            - проверяет, что в списке присутствуют все необходимые варианты;
            - проверяет, что в списке отсутствуют дополнительные варианты;
            - проверяет, что список отсортирован по алфавиту."""
        field = Ingredients._meta.get_field('measurement_unit')
        assert sorted(self.INGREDIENTS_VALID_UNITS) == field.choices
        return

    def test_invalid_name(self) -> None:
        """Тестирует создание объекта с невалидным значением поля "name"."""
        assert Ingredients.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Ingredients.objects.create(
                name=f'{"a"*49}',
                measurement_unit='шт.')
        assert str(err.value) == (
            "{'name': ['Убедитесь, что это значение содержит не более 48 "
            "символов (сейчас 49).']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_blank_fields(self) -> None:
        """Тестирует проверку пустых полей модели."""
        assert Ingredients.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Ingredients.objects.create(
                name='',
                measurement_unit='')
        assert str(err.value) == (
            "{'name': ['Это поле не может быть пустым.'], "
            "'measurement_unit': ['Это поле не может быть пустым.']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_null_fields(self) -> None:
        """Тестирует проверку незаполненных полей модели."""
        assert Ingredients.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Ingredients.objects.create(
                name=None,
                measurement_unit=None)
        assert str(err.value) == (
            "{'name': ['Это поле не может иметь значение NULL.'], "
            "'measurement_unit': "
            "['Это поле не может иметь значение NULL.']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_fields_unique(self) -> None:
        """Тестирует проверку уникальностей полей модели."""
        create_ingredient_obj(num=1)
        with pytest.raises(ValidationError) as err:
            create_ingredient_obj(num=1)
        assert str(err.value) == (
            "{'__all__': ['Ингредиент с такими значениями полей Название и "
            "Единица измерения уже существует.']}")
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        ingredient: Ingredients = create_ingredient_obj(num=1)
        assert str(ingredient) == 'test_ingredient_name_1 (батон)'
        assert ingredient._meta.ordering == ('name', )
        assert ingredient._meta.verbose_name == 'Ингредиент'
        assert ingredient._meta.verbose_name_plural == 'Ингредиенты'
        name = ingredient._meta.get_field('name')
        assert name.db_index
        assert name.verbose_name == 'Название'
        measurement_unit = ingredient._meta.get_field('measurement_unit')
        assert measurement_unit.verbose_name == 'Единица измерения'
        return


@pytest.mark.django_db
class TestTagsModel():
    """Производит тест модели "Ingredients"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        assert Tags.objects.all().count() == 0
        tag = create_tag_obj(num=1, unique_color='#000000')
        assert Tags.objects.all().count() == 1
        assert tag.name == 'Тег'
        assert tag.color == '#000000'
        assert tag.slug == 'test_tag_slug_1'
        return

    @pytest.mark.parametrize(
        'hex_code, error_message',
        [('',
          "{'color': ['Это поле не может быть пустым.']}"),
         (' ',
          "{'color': ['Введите корректный HEX цвет!']}"),
         ('rrr',
          "{'color': ['Введите корректный HEX цвет!']}"),
         ('00ffrf',
          "{'color': ['Введите корректный HEX цвет!']}"),
         ('#ff00ff00ff00',
          "{'color': ['Введите корректный HEX цвет!', 'Убедитесь, что это "
          "значение содержит не более 7 символов (сейчас 13).']}")])
    def test_invalid_hex_color(self, hex_code, error_message) -> None:
        """Тестирует регулярное выражение для HEX цвета поля "color"."""""
        with pytest.raises(ValidationError) as err:
            create_tag_obj(num=1, unique_color=hex_code)
        assert str(err.value) == error_message
        return

    @pytest.mark.parametrize(
        'invalid_name, error_message',
        [(f'{"a"*201}',
          "{'name': ['Введите корректное название тега (одно слово с "
          "заглавной буквы!', 'Убедитесь, что это значение содержит не "
          "более 200 символов (сейчас 201).']}"),
         ('',
          "{'name': ['Это поле не может быть пустым.']}")])
    def test_invalid_name(self, invalid_name, error_message) -> None:
        """Тестирует создание объекта с невалидным значением поля "name"."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='#000000',
                name=invalid_name,
                slug='slug')
        assert str(err.value) == error_message
        assert Tags.objects.all().count() == 0
        return

    def test_invalid_slug(self) -> None:
        """Тестирует создание объекта с невалидным значением поля "slug"."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='#000000',
                name='Тег',
                slug=f'{"a"*201}')
        assert str(err.value) == (
            "{'slug': ['Убедитесь, что это значение содержит не более 200 "
            "символов (сейчас 201).']}")
        assert Tags.objects.all().count() == 0
        return

    def test_blank_fields(self) -> None:
        """Тестирует проверку пустых полей модели."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='',
                name='',
                slug='')
        assert str(err.value) == (
            "{'color': ['Это поле не может быть пустым.'], "
            "'name': ['Это поле не может быть пустым.'], "
            "'slug': ['Это поле не может быть пустым.']}")
        assert Tags.objects.all().count() == 0
        return

    def test_null_fields(self) -> None:
        """Тестирует проверку незаполненных полей модели."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color=None,
                name=None,
                slug=None)
        assert str(err.value) == (
            "{'color': ['Это поле не может иметь значение NULL.'], "
            "'name': ['Это поле не может иметь значение NULL.'], "
            "'slug': ['Это поле не может иметь значение NULL.']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_fields_unique(self) -> None:
        """Тестирует проверку уникальностей полей модели."""
        create_tag_obj(num=1, unique_color='#000000')
        with pytest.raises(ValidationError) as err:
            create_tag_obj(num=1, unique_color='#000000')
        assert str(err.value) == (
            "{'color': ['Тег с таким HEX цвет уже существует.'], "
            "'name': ['Тег с таким Название уже существует.'], "
            "'slug': ['Тег с таким Краткий URL уже существует.']}")
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        tag: Tags = create_tag_obj(num=1)
        assert str(tag) == 'Тег (test_tag_slug_1)'
        assert tag._meta.ordering == ('name', )
        assert tag._meta.verbose_name == 'Тег'
        assert tag._meta.verbose_name_plural == 'Теги'
        color = tag._meta.get_field('color')
        assert color.unique
        assert color.verbose_name == 'HEX цвет'
        name = tag._meta.get_field('name')
        assert name.db_index
        assert name.unique
        assert name.verbose_name == 'Название'
        slug = tag._meta.get_field('slug')
        assert slug.unique
        assert slug.verbose_name == 'Краткий URL'
        return


@pytest.mark.django_db
class TestRecipesModel():
    """Производит тест модели "Ingredients"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        test_user = create_user_obj(num=1)
        assert Recipes.objects.all().count() == 0
        recipe = create_recipe_obj(num=1, user=test_user)
        assert Recipes.objects.all().count() == 1
        assert recipe.author == test_user
        assert recipe.cooking_time == 1
        assert recipe.image.read() == IMAGE_BYTES
        assert recipe.name == 'test_recipe_name_1'
        assert recipe.text == 'test_recipe_text_1'
        return

    def test_invalid_cooking_time(self) -> None:
        """Тестирует создание объекта с невалидным значением поля
        "cooking_time"."""
        test_user: User = create_user_obj(num=1)
        with pytest.raises(ValidationError) as err:
            Recipes.objects.create(
                author=test_user,
                cooking_time=0,
                name='test_recipe_name',
                text='test_recipe_text')
        assert str(err.value) == (
            "{'cooking_time': ['Время должно составлять не менее 1 минуты!'], "
            "'image': ['Это поле не может быть пустым.']}")
        return

    def test_invalid_name(self) -> None:
        """Тестирует создание объекта с невалидным значением поля "name"."""
        test_user: User = create_user_obj(num=1)
        assert Recipes.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Recipes.objects.create(
                author=test_user,
                cooking_time=1,
                name=f'{"a"*129}',
                text='test_recipe_text')
        assert str(err.value) == (
            "{'image': ['Это поле не может быть пустым.'], "
            "'name': ['Убедитесь, что это значение содержит не более 128 "
            "символов (сейчас 129).']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_blank_fields(self) -> None:
        """Тестирует проверку пустых полей модели."""
        test_user: User = create_user_obj(num=1)
        assert Recipes.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Recipes.objects.create(
                author=test_user,
                cooking_time='',
                name='',
                text='')
        assert str(err.value) == (
            "{'cooking_time': ['Значение “” должно быть целым числом.'], "
            "'image': ['Это поле не может быть пустым.'], "
            "'name': ['Это поле не может быть пустым.'], "
            "'text': ['Это поле не может быть пустым.']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_null_fields(self) -> None:
        """Тестирует проверку незаполненных полей модели."""
        assert Recipes.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Recipes.objects.create(
                author=None,
                cooking_time=None,
                image=None,
                name=None,
                text=None)
        assert str(err.value) == (
            "{'author': ['Это поле не может иметь значение NULL.'], "
            "'cooking_time': ['Это поле не может иметь значение NULL.'], "
            "'image': ['Это поле не может быть пустым.'], "
            "'name': ['Это поле не может иметь значение NULL.'], "
            "'text': ['Это поле не может иметь значение NULL.']}")
        assert Ingredients.objects.all().count() == 0
        return

    def test_fields_unique(self) -> None:
        """Тестирует проверку уникальностей полей модели."""
        test_user: User = create_user_obj(num=1)
        create_recipe_obj(num=1, user=test_user)
        with pytest.raises(ValidationError) as err:
            create_recipe_obj(num=1, user=test_user)
        assert str(err.value) == (
            "{'name': ['Рецепт с таким Название уже существует.']}")
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_user: User = create_user_obj(num=1)
        recipe: Recipes = create_recipe_obj(num=1, user=test_user)
        assert str(recipe) == 'test_recipe_name_1 (1 мин.)'
        assert recipe._meta.ordering == ('-id',)
        assert recipe._meta.verbose_name == 'Рецепт'
        assert recipe._meta.verbose_name_plural == 'Рецепты'
        author = recipe._meta.get_field('author')
        assert author.remote_field.on_delete == CASCADE
        assert author.remote_field.related_name == 'recipe_author'
        assert author.verbose_name == 'Автор'
        cooking_time = recipe._meta.get_field('cooking_time')
        assert cooking_time.verbose_name == 'Время приготовления (мин.)'
        image = recipe._meta.get_field('image')
        assert image.verbose_name == 'Картинка рецепта'
        ingredients = recipe._meta.get_field('ingredients')
        assert ingredients.verbose_name == 'Ингредиенты'
        name = recipe._meta.get_field('name')
        assert name.db_index
        assert name.unique
        assert name.verbose_name == 'Название'
        tags = recipe._meta.get_field('tags')
        assert tags.verbose_name == 'Теги'
        text = recipe._meta.get_field('text')
        assert text.verbose_name == 'Описание'
        return


@pytest.mark.django_db
class TestRecipesFavoritesModel():
    """Производит тест модели "RecipesFavorites"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        assert RecipesFavorites.objects.all().count() == 0
        recipe_favorite = create_recipe_favorite_obj(
            recipe=test_recipe_1, user=test_user_1)
        assert RecipesFavorites.objects.all().count() == 1
        assert recipe_favorite.user == test_user_1
        assert recipe_favorite.recipe == test_recipe_1
        return

    def test_unique_constraint(self) -> None:
        """Тестирует UniqueConstraint модели."""
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        assert RecipesFavorites.objects.all().count() == 0
        create_recipe_favorite_obj(recipe=test_recipe_1, user=test_user_1)
        assert RecipesFavorites.objects.all().count() == 1
        with pytest.raises(ValidationError) as err:
            create_recipe_favorite_obj(recipe=test_recipe_1, user=test_user_1)
        assert str(err.value) == (
            "{'__all__': ['Избранный рецепт с такими значениями полей "
            "Пользователь и Рецепт уже существует.']}")
        assert RecipesFavorites.objects.all().count() == 1
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        recipe_favorite = create_recipe_favorite_obj(
            recipe=test_recipe_1, user=test_user_1)
        assert str(recipe_favorite) == (
            'test_user_username_1: "test_recipe_name_1 (1 мин.)"')
        assert recipe_favorite._meta.ordering == ('-id', )
        assert recipe_favorite._meta.verbose_name == 'Избранный рецепт'
        assert recipe_favorite._meta.verbose_name_plural == 'Избранные рецепты'
        user = recipe_favorite._meta.get_field('user')
        assert user.remote_field.on_delete == CASCADE
        assert user.remote_field.related_name == 'user_recipe_favorite'
        assert user.verbose_name == 'Пользователь'
        recipe = recipe_favorite._meta.get_field('recipe')
        assert recipe.remote_field.on_delete == CASCADE
        assert recipe.remote_field.related_name == 'recipe_favorite_user'
        assert recipe.verbose_name == 'Рецепт'
        return


@pytest.mark.django_db
class TestRecipesIngredientsModel():
    """Производит тест модели "RecipesIngredients"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        test_ingredient_1: Ingredients = create_ingredient_obj(num=1)
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        TEST_AMOUNT: float = 0.3
        assert RecipesIngredients.objects.all().count() == 0
        recipe_ingredient = create_recipe_ingredient_obj(
            amount=TEST_AMOUNT,
            ingredient=test_ingredient_1,
            recipe=test_recipe_1)
        assert RecipesIngredients.objects.all().count() == 1
        assert recipe_ingredient.amount == TEST_AMOUNT
        assert recipe_ingredient.ingredient == test_ingredient_1
        assert recipe_ingredient.recipe == test_recipe_1
        return

    def test_invalid_amount(self) -> None:
        """Тестирует создание объекта с невалидным значением поля "amount"."""
        test_ingredient_1: Ingredients = create_ingredient_obj(num=1)
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        with pytest.raises(ValidationError) as err:
            RecipesIngredients.objects.create(
                amount='один',
                ingredient=test_ingredient_1,
                recipe=test_recipe_1)
        assert str(err.value) == (
            "{'amount': "
            "['Значение “один” должно быть числом с плавающей точкой.']}")
        return

    def test_unique_constraint(self) -> None:
        """Тестирует UniqueConstraint модели."""
        test_ingredient_1: Ingredients = create_ingredient_obj(num=1)
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        TEST_AMOUNT: float = 0.3
        assert RecipesIngredients.objects.all().count() == 0
        create_recipe_ingredient_obj(
            amount=TEST_AMOUNT,
            ingredient=test_ingredient_1,
            recipe=test_recipe_1)
        assert RecipesIngredients.objects.all().count() == 1
        with pytest.raises(ValidationError) as err:
            create_recipe_ingredient_obj(
                amount=TEST_AMOUNT,
                ingredient=test_ingredient_1,
                recipe=test_recipe_1)
        assert str(err.value) == (
            "{'__all__': [\'Связь моделей \"Рецепты\" и \"Ингредиенты\" "
            "с такими значениями полей Ингредиент и Рецепт уже существует.']}")
        assert RecipesIngredients.objects.all().count() == 1
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_ingredient_1: Ingredients = create_ingredient_obj(num=1)
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        TEST_AMOUNT: float = 0.3
        assert RecipesIngredients.objects.all().count() == 0
        recipe_ingredient = create_recipe_ingredient_obj(
            amount=TEST_AMOUNT,
            ingredient=test_ingredient_1,
            recipe=test_recipe_1)
        assert str(recipe_ingredient) == (
            'test_recipe_name_1 - test_ingredient_name_1')
        assert recipe_ingredient._meta.ordering == ('recipe', 'ingredient')
        assert recipe_ingredient._meta.verbose_name == (
            'Связь моделей "Рецепты" и "Ингредиенты"')
        assert recipe_ingredient._meta.verbose_name_plural == (
            'Связи моделей "Рецепты" и "Ингредиенты"')
        amount = recipe_ingredient._meta.get_field('amount')
        assert amount.verbose_name == 'Количество'
        ingredient = recipe_ingredient._meta.get_field('ingredient')
        assert ingredient.remote_field.on_delete == CASCADE
        assert ingredient.remote_field.related_name == 'ingredient_recipe'
        assert ingredient.verbose_name == 'Ингредиент'
        recipe = recipe_ingredient._meta.get_field('recipe')
        assert recipe.remote_field.on_delete == CASCADE
        assert recipe.remote_field.related_name == 'recipe_ingredient'
        assert recipe.verbose_name == 'Рецепт'
        return


@pytest.mark.django_db
class TestRecipesTagsModel():
    """Производит тест модели "RecipesTags"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        test_tag_1: Tags = create_tag_obj(num=1)
        assert RecipesTags.objects.all().count() == 0
        recipe_tag = create_recipe_tag_obj(
            recipe=test_recipe_1,
            tag=test_tag_1)
        assert RecipesTags.objects.all().count() == 1
        assert recipe_tag.recipe == test_recipe_1
        assert recipe_tag.tag == test_tag_1
        return

    def test_unique_constraint(self) -> None:
        """Тестирует UniqueConstraint модели."""
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        test_tag_1: Tags = create_tag_obj(num=1)
        assert RecipesTags.objects.all().count() == 0
        create_recipe_tag_obj(recipe=test_recipe_1, tag=test_tag_1)
        assert RecipesTags.objects.all().count() == 1
        with pytest.raises(ValidationError) as err:
            create_recipe_tag_obj(recipe=test_recipe_1, tag=test_tag_1)
        assert str(err.value) == (
            "{'__all__': [\'Связь моделей \"Рецепты\" и \"Теги\" "
            "с такими значениями полей Рецепт и Тег уже существует.']}")
        assert RecipesTags.objects.all().count() == 1

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_user_1: User = create_user_obj(num=1)
        test_recipe_1: Recipes = create_recipe_obj(num=1, user=test_user_1)
        test_tag_1: Tags = create_tag_obj(num=1)
        assert RecipesTags.objects.all().count() == 0
        recipe_tag = create_recipe_tag_obj(
            recipe=test_recipe_1,
            tag=test_tag_1)
        assert str(recipe_tag) == (
            'test_recipe_name_1 - Тег')
        assert recipe_tag._meta.ordering == ('recipe', 'tag')
        assert recipe_tag._meta.verbose_name == (
            'Связь моделей "Рецепты" и "Теги"')
        assert recipe_tag._meta.verbose_name_plural == (
            'Связи моделей "Рецепты" и "Теги"')
        recipe = recipe_tag._meta.get_field('recipe')
        assert recipe.null
        assert recipe.remote_field.on_delete == SET_NULL
        assert recipe.remote_field.related_name == 'recipe_tag'
        assert recipe.verbose_name == 'Рецепт'
        tag = recipe_tag._meta.get_field('tag')
        assert tag.null
        assert tag.remote_field.on_delete == SET_NULL
        assert tag.remote_field.related_name == 'tag_recipe'
        assert tag.verbose_name == 'Тег'
        return


@pytest.mark.django_db
class TestShoppingCartsModel():
    """Производит тест модели "ShoppingCarts"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        test_user: User = create_user_obj(num=1)
        test_recipe: Recipes = create_recipe_obj(num=1, user=test_user)
        assert ShoppingCarts.objects.all().count() == 0
        shopping_cart = create_shopping_cart_obj(
            recipe=test_recipe, user=test_user)
        assert ShoppingCarts.objects.all().count() == 1
        assert shopping_cart.user == test_user
        assert shopping_cart.recipe == test_recipe
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_user: User = create_user_obj(num=1)
        test_recipe: Recipes = create_recipe_obj(num=1, user=test_user)
        shopping_cart: ShoppingCarts = create_shopping_cart_obj(
            recipe=test_recipe, user=test_user)
        assert str(shopping_cart) == (
            'test_user_username_1: "test_recipe_name_1 (1 мин.)"')
        assert shopping_cart._meta.ordering == ('user', 'recipe')
        assert shopping_cart._meta.verbose_name == 'Список покупок'
        assert shopping_cart._meta.verbose_name_plural == 'Списки покупок'
        user = shopping_cart._meta.get_field('user')
        assert user.remote_field.on_delete == CASCADE
        assert user.remote_field.related_name == 'shopping_cart'
        assert user.verbose_name == 'Корзина пользователя'
        recipe = shopping_cart._meta.get_field('recipe')
        assert recipe.null
        assert recipe.remote_field.on_delete == SET_NULL
        assert recipe.remote_field.related_name == 'shopping_cart'
        assert recipe.verbose_name == 'Рецепт в корзине'
        return


@pytest.mark.django_db
class TestSubscriptionsModel():
    """Производит тест модели "Subscriptions"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        test_user_1: User = create_user_obj(num=1)
        test_user_2: User = create_user_obj(num=2)
        assert Subscriptions.objects.all().count() == 0
        subscription = create_subscription_obj(
            subscriber=test_user_1, subscription_to=test_user_2)
        assert Subscriptions.objects.all().count() == 1
        assert subscription.subscriber == test_user_1
        assert subscription.subscription_to == test_user_2
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_user_1: User = create_user_obj(num=1)
        test_user_2: User = create_user_obj(num=2)
        subscription = create_subscription_obj(
            subscriber=test_user_1, subscription_to=test_user_2)
        assert str(subscription) == (
            'Подписка test_user_username_1 на test_user_username_2')
        assert subscription._meta.ordering == ('-id', )
        assert subscription._meta.verbose_name == 'Подписка'
        assert subscription._meta.verbose_name_plural == 'Подписки на авторов'
        subscriber = subscription._meta.get_field('subscriber')
        assert subscriber.remote_field.on_delete == CASCADE
        assert subscriber.remote_field.related_name == 'subscriber'
        assert subscriber.verbose_name == 'Подписчик'
        subscription_to = subscription._meta.get_field('subscription_to')
        assert subscription_to.remote_field.on_delete == CASCADE
        assert subscription_to.remote_field.related_name == (
            'subscription_author')
        assert subscription_to.verbose_name == 'Автор на которого подписка'
        return


def test_delete_temp_media_folder() -> None:
    """Проверяет, что папка с тестовыми медиа-данными успешно удалена."""
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    assert not os.path.exists(settings.MEDIA_ROOT)
    return
