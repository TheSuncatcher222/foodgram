import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import CASCADE

from footgram_app.models import (
    Ingredients, Recipes, RecipesFavoritesUsers, RecipesIngredients,
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

FAVORITES_VALID_OBJ = lambda user, recipe: (
    RecipesFavoritesUsers.objects.create(
        user=user,
        recipe=recipe))


def create_ingredients_obj(num: int) -> Ingredients:
    """Создает и возвращает объект модели "Ingredients"."""
    return Ingredients.objects.create(
        name=f'test_name_{num}',
        measurement_unit='батон')


RECIPES_INGREDIENTS_VALID_OBJ = lambda ingredient, recipe: (
    RecipesIngredients.objects.create(
        ingredient=ingredient,
        recipe=recipe))
RECIPES_TAGS_VALID_OBJ = lambda recipe, tag: (
    RecipesTags.objects.create(
        recipe=recipe,
        tag=tag))


def create_recipes_obj(
        num: int, user: User, image_code: bytes = IMAGE_BYTES) -> None:
    """Создает и возвращает объект модели "Recipes".
    Изображения сохраняются в отдельную субдиректорию медиа для тестов."""
    image_file: ContentFile = ContentFile(image_code)
    uploaded_image: SimpleUploadedFile = SimpleUploadedFile(
        f'test_image_{num}.gif', image_file.read(), content_type='image/gif')
    recipe: Recipes = Recipes.objects.create(
        author=user,
        cooking_time=num,
        image=uploaded_image,
        name=f'test_name_{num}',
        text=f'test_text_{num}')
    return recipe


SHOPPING_CARTS_VALID_OBJ = lambda user, recipe: (
    ShoppingCarts.objects.create(
        user=user,
        cart_item=recipe))
SUBSCRIPTIONS_VALID_OBJ = lambda subscriber, subscription_to: (
    Subscriptions.objects.create(
        subscriber=subscriber,
        subscription_to=subscription_to))


def create_tags_obj(num: int, unique_color: str) -> Tags:
    """Создает и возвращает объект модели "Tags"."""
    return Tags.objects.create(
        color=unique_color,
        name=f'test_name_{num}',
        slug=f'test_slug_{num}')


def create_user_obj(num: int) -> User:
    return User.objects.create(
        email=f'test_email_{num}@email.com',
        username=f'test_username_{num}',
        first_name=f'test_first_name_{num}',
        last_name=f'test_last_name_{num}',
        password=f'test_password_{num}')


@pytest.fixture(autouse=True)
def test_override_media_root(settings) -> None:
    """Фикстура, перезаписывающая путь папки "MEDIA_ROOT"."""
    settings.MEDIA_ROOT = settings.MEDIA_ROOT / IMAGE_TEST_FOLDER
    return


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
        assert ingredient.name == 'test_name_1'
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

    def test_null_fields(self) -> None:
        """Тестирует проверку незаполненных полей модели."""
        assert Ingredients.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Ingredients.objects.create(
                name=None,
                measurement_unit=None)
        assert str(err.value) == (
            "{'name': ['Это поле не может иметь значение NULL.'], "
            "'measurement_unit': ['Это поле не может иметь значение NULL.']}")
        assert Ingredients.objects.all().count() == 0

    def test_fields_unique(self) -> None:
        """Тестирует проверку уникальностей полей модели."""
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
        assert str(ingredient) == 'test_name_1 (батон)'
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
        assert tag.name == 'test_name_1'
        assert tag.color == '#000'
        assert tag.slug == 'test_slug_1'
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
        """Тестирует создание объекта с невалидным значением поля "name"."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='#000',
                name=invalid_name,
                slug='slug')
        assert str(err.value) == error_message
        assert Tags.objects.all().count() == 0
        return

    def test_invalid_slug(self) -> None:
        """Тестирует создание объекта с невалидным значением поля "name"."""
        assert Tags.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Tags.objects.create(
                color='#000',
                name='tag',
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

    def test_fields_unique(self) -> None:
        """Тестирует проверку уникальностей полей модели."""
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
        assert str(tag) == 'test_name_1 (test_slug_1)'
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
        recipe = create_recipes_obj(num=1, user=test_user)
        assert Recipes.objects.all().count() == 1
        assert recipe.author == test_user
        assert recipe.cooking_time == 1
        assert recipe.image.read() == IMAGE_BYTES
        assert recipe.name == 'test_name_1'
        assert recipe.text == 'test_text_1'
        return

    def test_invalid_cooking_time(self) -> None:
        """Тестирует создание объекта с невалидным значением поля
        "cooking_time".
        Поле "image" оставляет пустым для упрощения теста."""
        test_user: User = create_user_obj(num=1)
        with pytest.raises(ValidationError) as err:
            Recipes.objects.create(
                author=test_user,
                cooking_time=0,
                name='test_name',
                text='test_text')
        assert str(err.value) == (
            "{'cooking_time': ['Убедитесь, что это значение больше либо "
            "равно 1.'], "
            "'image': ['Это поле не может быть пустым.']}")
        return

    def test_invalid_name(self) -> None:
        """Тестирует создание объекта с невалидным значением поля "name".
        Поле "image" оставляет пустым для упрощения теста."""
        test_user: User = create_user_obj(num=1)
        assert Recipes.objects.all().count() == 0
        with pytest.raises(ValidationError) as err:
            Recipes.objects.create(
                author=test_user,
                cooking_time=1,
                name=f'{"a"*129}',
                text='test_text')
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

    def test_fields_unique(self) -> None:
        """Тестирует проверку уникальностей полей модели."""
        test_user: User = create_user_obj(num=1)
        create_recipes_obj(num=1, user=test_user)
        with pytest.raises(ValidationError) as err:
            create_recipes_obj(num=1, user=test_user)
        assert str(err.value) == (
            "{'name': ['Рецепт с таким Название уже существует.']}")
        return

    def test_meta(self) -> None:
        """Тестирует мета-данные модели и полей.
        Тестирует строковое представление модели."""
        test_user: User = create_user_obj(num=1)
        recipe: Recipes = create_recipes_obj(num=1, user=test_user)
        assert str(recipe) == 'test_name_1 (1 мин.)'
        assert recipe._meta.ordering == ('-id',)
        assert recipe._meta.verbose_name == 'Рецепт'
        assert recipe._meta.verbose_name_plural == 'Рецепты'
        author = recipe._meta.get_field('author')
        assert author.remote_field.on_delete == CASCADE
        assert author.remote_field.related_name == 'recipe_author'
        assert author.verbose_name == 'Автор'
        cooking_time = recipe._meta.get_field('cooking_time')
        assert cooking_time.verbose_name == 'Время приготовления (в минутах)'
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
