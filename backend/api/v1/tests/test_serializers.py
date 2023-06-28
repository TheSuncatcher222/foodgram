import pytest

from rest_framework.serializers import (
    Serializer, ListSerializer,
    Field,
    BooleanField, CharField, ChoiceField, ImageField, FloatField,
    EmailField, IntegerField, SerializerMethodField, SlugField)
from api.v1.serializers import (
    CustomUserSerializer, CustomUserSubscriptionsSerializer,
    IngredientsSerializer, PrimaryKeyRelatedField, RecipesSerializer,
    RecipesIngredientsSerializer, RecipesIngredientsCreateSerializer,
    RecipesFavoritesSerializer, RecipesShortSerializer,
    ShoppingCartsSerializer, SubscriptionsSerializer,
    TagsIdListSerializer, TagsSerializer)


def serializer_fields_check(
        expected_fields: dict[str, Field],
        serializer: Serializer) -> None:
    """Тестирует поля указанного сериализатора."""
    assert list(serializer.fields.keys()) == list(expected_fields.keys())
    for field, field_type in expected_fields.items():
        assert isinstance(serializer.fields[field], field_type)
    return


def test_custom_user_serializer() -> None:
    """Тестирует поля сериализатора "CustomUserSerializer"."""
    expected_fields: dict[str, any] = {
        'email': EmailField,
        'id': IntegerField,
        'username': CharField,
        'first_name': CharField,
        'last_name': CharField,
        'password': CharField,
        'is_subscribed': SerializerMethodField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=CustomUserSerializer())
    return


def test_custom_user_subscriptions_serializer() -> None:
    """Тестирует поля сериализатора "CustomUserSubscriptionsSerializer"."""
    expected_fields = {
        'email': EmailField,
        'id': IntegerField,
        'username': CharField,
        'first_name': CharField,
        'last_name': CharField,
        'is_subscribed': BooleanField,
        'recipes_count': SerializerMethodField,
        'recipes': ListSerializer}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=CustomUserSubscriptionsSerializer())
    return


def test_ingredients_serializer() -> None:
    """Тестирует поля сериализатора "IngredientsSerializer"."""
    expected_fields = {
        'id': IntegerField,
        'name': CharField,
        'measurement_unit': ChoiceField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=IngredientsSerializer())
    return


# ToDo: выполнить указание в @pytest.mark и запустить тест
@pytest.mark.skip(reason=(
    "Test will be failed. Need to replace \"self.context['request'].method\""
    "in serializers.py with \"self.context['request_method']\""))
def test_recipes_serializer() -> None:
    """Тестирует поля сериализатора "RecipesSerializer"."""
    expected_fields = {
        'id': IntegerField,
        'tags': ListSerializer,
        'author': PrimaryKeyRelatedField,
        'ingredients': ListSerializer,
        'is_favorited': BooleanField,
        'is_in_shopping_cart': BooleanField,
        'name': CharField,
        'image': ImageField,
        'text': CharField,
        'cooking_time': IntegerField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=RecipesSerializer(request={'request_method': 'GET'}))
    return


def test_recipes_ingredients_serializer() -> None:
    """Тестирует поля сериализатора "RecipesIngredientsSerializer"."""
    expected_fields = {
        'id': IntegerField,
        'name': CharField,
        'measurement_unit': CharField,
        'amount': FloatField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=RecipesIngredientsSerializer())
    return


def test_recipes_ingredients_create_serializer() -> None:
    """Тестирует поля сериализатора "RecipesIngredientsCreateSerializer"."""
    expected_fields = {
        'id': PrimaryKeyRelatedField,
        'name': SerializerMethodField,
        'measurement_unit': SerializerMethodField,
        'amount': FloatField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=RecipesIngredientsCreateSerializer())
    return


def test_recipes_favorites_serializer() -> None:
    """Тестирует поля сериализатора "RecipesFavoritesSerializer"."""
    expected_fields = {
        'user': PrimaryKeyRelatedField,
        'recipe': PrimaryKeyRelatedField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=RecipesFavoritesSerializer())
    return


def test_recipes_short_serializer() -> None:
    """Тестирует поля сериализатора "RecipesShortSerializer"."""
    expected_fields = {
        'id': IntegerField,
        'name': CharField,
        'image': ImageField,
        'cooking_time': IntegerField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=RecipesShortSerializer())
    return


def test_shopping_carts_serializer() -> None:
    """Тестирует поля сериализатора "ShoppingCartsSerializer"."""
    expected_fields = {
        'user': PrimaryKeyRelatedField,
        'recipe': PrimaryKeyRelatedField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=ShoppingCartsSerializer())
    return


def test_subscriptions_serializer() -> None:
    """Тестирует поля сериализатора "SubscriptionsSerializer"."""
    expected_fields = {
        'subscriber': PrimaryKeyRelatedField,
        'subscription_to': PrimaryKeyRelatedField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=SubscriptionsSerializer())
    return


def test_tags_serializer() -> None:
    """Тестирует поля сериализатора "TagsSerializer"."""
    expected_fields = {
        'id': IntegerField,
        'name': CharField,
        'color': CharField,
        'slug': SlugField}
    serializer_fields_check(
        expected_fields=expected_fields,
        serializer=TagsSerializer())
    return


def test_tags_id_list_serializer() -> None:
    """Тестирует поля сериализатора "TagsIdListSerializer".
    Сериализатор представляет собой объект "ListField"."""
    serializer: Field = TagsIdListSerializer()
    assert isinstance(serializer.child, IntegerField)
