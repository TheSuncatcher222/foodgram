import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from footgram_app.models import (
    UNITS,
    Ingredients, Recipes, RecipesFavoritesUsers, RecipesIngredients,
    RecipesTags, ShoppingCarts, Subscriptions, Tags)

TEST_OBJECTS_COUNT: int = 2

MAX_LENGTH_INGREDIENTS_NAME: int = 48
MAX_LENGTH_INGREDIENTS_UNIT: int = 48
MAX_LENGTH_TAGS_COLOR: int = 7
MAX_LENGTH_TAGS_NAME: int = 32
MAX_LENGTH_RECIPES_NAME: int = 128


def create_ingredients_obj(num: int):
    """Создает и возвращает объект модели "Ingredients"."""
    return Ingredients.objects.create(
        name=f'test_ingredient_{num}',
        measurement_unit='батон')


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

    def test_valid_choices(self) -> None:
        """Тестирует список выбора choices поля "measurement_unit":
            - проверяет, что в списке присутствуют все необходимые варианты;
            - проверяет, что в списке отсутствуют дополнительные варианты;
            - проверяет, что список отсортирован по алфавиту."""
        field = Ingredients._meta.get_field('measurement_unit')
        assert sorted(self.INGREDIENTS_VALID_UNITS) == field.choices

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
        with pytest.raises(ValidationError) as e:
            Ingredients.objects.create(
                name=invalid_name,
                measurement_unit='шт.')
        assert str(e.value) == error_message
        assert Ingredients.objects.all().count() == 0

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        ingredient: Ingredients = create_ingredients_obj(num=1)
        assert str(ingredient) == 'test_ingredient_1 (батон)'
        assert ingredient._meta.ordering == ('name', )
        assert ingredient._meta.verbose_name == 'ингредиент'
        assert ingredient._meta.verbose_name_plural == 'ингредиенты'
        name = ingredient._meta.get_field('name')
        assert name.db_index == True
        assert name.verbose_name == 'Название'
        assert name.unique == True
        measurement_unit = ingredient._meta.get_field('measurement_unit')
        assert measurement_unit.verbose_name == 'Единица измерения'
