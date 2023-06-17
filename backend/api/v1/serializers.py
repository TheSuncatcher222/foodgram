"""
Создает сериализаторы моделей проекта "Footgram".

Классы-сериализаторы:
    - CustomUserSerializer (унаследован от UserSerializer)

Создает ограничения для вводимых полей модели:
    - USER_EMAIL_MAX_LEN - максимальная длина поля "email";
    - USER_FIRST_NAME_MAX_LEN - максимальная длина поля "first_name";
    - USER_PASSWORD_MAX_LEN - максимальная длина поля "password";
    - USER_SECOND_NAME_MAX_LEN - максимальная длина поля "second_name";
    - USER_USERNAME_MAX_LEN - максимальная длина поля "username";
    - USER_FORBIDDEN_USERNAMES - список запрещенных значений поля "username";
    - USERNAME_PATTERN - паттерн допустимых символов поля "username".
"""

from django.contrib.auth.models import User
from djoser.serializers import UserSerializer
from re import sub
from rest_framework.serializers import (
    ModelSerializer,
    EmailField, CharField, SerializerMethodField,
    ValidationError)

from footgram_app.models import Ingredients, Subscriptions

USER_EMAIL_MAX_LEN: int = 254
USER_FIRST_NAME_MAX_LEN: int = 150
USER_PASSWORD_MAX_LEN: int = 150
USER_SECOND_NAME_MAX_LEN: int = 150
USER_USERNAME_MAX_LEN: int = 150

USER_FORBIDDEN_USERNAMES: list[str] = ['me']

USERNAME_PATTERN: str = r'^[\w.@+-]+$'


class CustomUserSerializer(UserSerializer):
    """Переопределяет UserSerializer библиотеки Djoser:
        - добавляет поле 'is_subscribed' в конец списка полей;
        - делает обязательными для заполнения поля:
            - 'email';
            - 'first_name';
            - 'last_name';
        - производит валидацию на уникальность поля 'email'."""
    email = EmailField(max_length=USER_EMAIL_MAX_LEN)
    is_subscribed = SerializerMethodField()
    password = CharField(
        max_length=USER_PASSWORD_MAX_LEN,
        write_only=True)
    username = CharField(max_length=USER_USERNAME_MAX_LEN)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'required': True}}

    def get_is_subscribed(self, obj):
        """Показывает статус подписки пользователя в поле 'is_subscribed'.
        Возвращает True, если пользователь имеет подписку, False - если не
        имеет, или пользователь не авторизован."""
        if self.context['request'].user.is_anonymous:
            return False
        else:
            return Subscriptions.objects.filter(
                subscriber=self.context['request'].user,
                subscription_to=obj).exists()

    def validate_email(self, value):
        """Производит валидацию поля 'email':
            - проверяет на уникальность."""
        if User.objects.filter(email=value).exists():
            raise ValidationError(
                'Пользователь с такой электронной почтой уже существует.')
        return value

    def validate_username(self, value):
        """Производит валидацию поля 'email':
            - проверяет на уникальность;
            - проверяет на несоответствие запрещенным именам."""
        forbidden_chars: str = sub(
            pattern=USERNAME_PATTERN,
            repl='',
            string=value)
        if forbidden_chars:
            sort_chars: str = ', '.join(
                f'"{c}"' for c in sorted(set(forbidden_chars)))
            raise ValidationError(
                f'Использование {sort_chars} в имени пользователя запрещено.')
        for forbidden in USER_FORBIDDEN_USERNAMES:
            if value.lower() == forbidden.lower():
                raise ValidationError(
                    f'Пользователь с именем "{forbidden}" недопустим.')
        if User.objects.filter(username=value).exists():
            raise ValidationError(
                'Пользователь с таким именем уже существует.')
        return value


class IngredientsSerializer(ModelSerializer):
    """Создает сериализатор для модели "Ingredients"."""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit')
