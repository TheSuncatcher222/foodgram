import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from footgram_app.models import (
    Ingredients, Recipes, RecipesFavoritesUsers, RecipesIngredients,
    RecipesTags, ShoppingCarts, Subscriptions, Tags)

TEST_OBJECTS_COUNT: int = 2

MAX_LENGTH_INGREDIENTS_NAME: int = 48
MAX_LENGTH_INGREDIENTS_UNIT: int = 48
MAX_LENGTH_TAGS_COLOR: int = 7
MAX_LENGTH_TAGS_NAME: int = 32
MAX_LENGTH_RECIPES_NAME: int = 128


def create_ingredients_obj(num: int) -> Ingredients:
    """Создает и возвращает объект модели "Ingredients"."""
    return Ingredients.objects.create(
        name=f'test_ingredient_{num}',
        measurement_unit='батон')


def create_tags_obj(num: int, unique_color: str) -> Tags:
    """Создает и возвращает объект модели "Tags"."""
    return Tags.objects.create(
        color=unique_color,
        name=f'test_tag_{num}',
        slug=f'test_tag_slug_{num}')


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
        ingredient: Ingredients = create_ingredients_obj(num=1)
        assert Ingredients.objects.all().count() == 1
        assert ingredient.name == 'test_ingredient_1'
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

    @pytest.mark.parametrize(
        'invalid_name, error_message',
        [(f'{"a"*49}',
          "{'name': ['Убедитесь, что это значение содержит не более 48 "
          "символов (сейчас 49).']}"),
         ('',
          "{'name': ['Это поле не может быть пустым.']}")])
    def test_invalid_name(self, invalid_name, error_message) -> None:
        """Тестирует создание объекта с невалидным значением поля 'name'."""
        assert Ingredients.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Ingredients.objects.create(
                name=invalid_name,
                measurement_unit='шт.')
        assert str(err.value) == error_message
        assert Ingredients.objects.all().count() == 0
        return

    def test_fields_unique(self):
        create_ingredients_obj(num=1)
        with pytest.raises(ValidationError) as err:
            create_ingredients_obj(num=1)
        assert str(err.value) == (
            "{'name': ['Ингредиент с таким Название уже существует.']}")
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        ingredient: Ingredients = create_ingredients_obj(num=1)
        assert str(ingredient) == 'test_ingredient_1 (батон)'
        assert ingredient._meta.ordering == ('name', )
        assert ingredient._meta.verbose_name == 'ингредиент'
        assert ingredient._meta.verbose_name_plural == 'ингредиенты'
        name = ingredient._meta.get_field('name')
        assert name.db_index
        assert name.verbose_name == 'Название'
        assert name.unique
        measurement_unit = ingredient._meta.get_field('measurement_unit')
        assert measurement_unit.verbose_name == 'Единица измерения'
        return


@pytest.mark.django_db
class TestTagsModel():
    """Производит тест модели "Ingredients"."""

    def test_valid_create(self) -> None:
        """Тестирует возможность создания объекта с валидными данными."""
        assert Tags.objects.all().count() == 0
        tag = create_tags_obj(num=1, unique_color='#000')
        assert Tags.objects.all().count() == 1
        assert tag.name == 'test_tag_1'
        assert tag.color == '#000'
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
            create_tags_obj(num=1, unique_color=hex_code)
        assert str(err.value) == error_message
        return

    @pytest.mark.parametrize(
        'invalid_name, error_message',
        [(f'{"a"*201}',
          "{'name': ['Убедитесь, что это значение содержит не более 200 "
          "символов (сейчас 201).']}"),
         ('',
          "{'name': ['Это поле не может быть пустым.']}")])
    def test_invalid_name(self, invalid_name, error_message) -> None:
        """Тестирует создание объекта с невалидным значением поля 'name'."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='#000',
                name=invalid_name,
                slug='slug')
        assert str(err.value) == error_message
        assert Tags.objects.all().count() == 0
        return

    @pytest.mark.parametrize(
        'invalid_slug, error_message',
        [(f'{"a"*201}',
          "{'slug': ['Убедитесь, что это значение содержит не более 200 "
          "символов (сейчас 201).']}"),
         ('',
          "{'slug': ['Это поле не может быть пустым.']}")])
    def test_invalid_slug(self, invalid_slug, error_message) -> None:
        """Тестирует создание объекта с невалидным значением поля 'name'."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='#000',
                name='tag',
                slug=invalid_slug)
        assert str(err.value) == error_message
        assert Tags.objects.all().count() == 0
        return

    def test_fields_unique(self):
        create_tags_obj(num=1, unique_color='#000')
        with pytest.raises(ValidationError) as err:
            create_tags_obj(num=1, unique_color='#000')
        assert str(err.value) == (
            "{'color': ['Тег с таким HEX цвет уже существует.'], "
            "'name': ['Тег с таким Название уже существует.'], "
            "'slug': ['Тег с таким Краткий URL уже существует.']}")
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        tag: Tags = create_tags_obj(num=1, unique_color='#000')
        assert str(tag) == 'test_tag_1 (test_tag_slug_1)'
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
