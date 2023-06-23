from rest_framework.serializers import (
    Serializer, ListSerializer,
    Field,
    SerializerMethodField,
    BooleanField, CharField, ChoiceField, EmailField, IntegerField,
    SlugField)

from api.v1.serializers import (
    CustomUserSerializer, CustomUserSubscriptionsSerializer,
    IngredientsSerializer, PrimaryKeyRelatedField, ShoppingCartsSerializer,
    SubscriptionsSerializer, TagsIdListSerializer, TagsSerializer)


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
    expected_fields: dict[str, any] = {
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


"""В разработке."""


# ToDo: разработать тест
def test_recipes_serializer_subscriptions_serializer() -> None:
    """Тестирует поля сериализатора "RecipesSerializerSubscriptions"."""
    pass


# ToDo: разработать тест
def test_recipes_ingredients_serializer() -> None:
    """Тестирует поля сериализатора "RecipesIngredientsSerializer"."""
    pass


# ToDo: разработать тест
def test_recipes_ingredients_create_serializer() -> None:
    """Тестирует поля сериализатора "RecipesIngredientsCreateSerializer"."""
    pass


# ToDo: разработать тест
def test_recipes_serializer() -> None:
    """Тестирует поля сериализатора "RecipesSerializer"."""
    pass


# ToDo: разработать тест
def test_recipes_favorites_serializer() -> None:
    """Тестирует поля сериализатора "RecipesFavoritesSerializer"."""
    pass
