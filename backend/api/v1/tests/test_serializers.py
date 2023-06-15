from rest_framework.serializers import (
    CharField, EmailField, IntegerField, SerializerMethodField)

from api.v1.serializers import CustomUserSerializer


def test_custom_user_serializer():
    expected_fields = {
        'email': EmailField,
        'id': IntegerField,
        'username': CharField,
        'first_name': CharField,
        'last_name': CharField,
        'password': CharField,
        'is_subscribed': SerializerMethodField}
    serializer = CustomUserSerializer()
    assert list(serializer.fields.keys()) == list(expected_fields.keys())
    for field, field_type in expected_fields.items():
        assert isinstance(serializer.fields[field], field_type)
