from rest_framework.serializers import (
    CharField, ChoiceField, EmailField, IntegerField, SerializerMethodField)

from api.v1.serializers import CustomUserSerializer, IngredientsSerializer


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
    serializer: CustomUserSerializer = CustomUserSerializer()
    assert list(serializer.fields.keys()) == list(expected_fields.keys())
    for field, field_type in expected_fields.items():
        assert isinstance(serializer.fields[field], field_type)


def test_ingredients_serializer() -> None:
    """Тестирует поля сериализатора "IngredientsSerializer"."""
    expected_fields = {
        'id': IntegerField,
        'name': CharField,
        'measurement_unit': ChoiceField}
    serializer: IngredientsSerializer = IngredientsSerializer()
    assert list(serializer.fields.keys()) == list(expected_fields.keys())
    for field, field_type in expected_fields.items():
        assert isinstance(serializer.fields[field], field_type)
