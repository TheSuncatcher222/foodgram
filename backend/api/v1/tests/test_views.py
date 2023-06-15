
import json

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from api.v1.serializers import (
    USER_EMAIL_MAX_LEN, USER_FIRST_NAME_MAX_LEN, USER_PASSWORD_MAX_LEN,
    USER_SECOND_NAME_MAX_LEN, USER_USERNAME_MAX_LEN)

USERS_URL: str = '/api/v1/users/'

TEST_USER: User = lambda i: User.objects.create(
    email=f'test_user_{i}@email.com',
    username=f'test_user_{i}',
    first_name=f'test_user_{i}_first_name',
    last_name=f'test_user_{i}_last_name')
TEST_USERS_COUNT: int = 3


@pytest.fixture()
def create_users() -> None:
    """Фикстура для наполнения БД заданным числом пользователей."""
    for i in range(TEST_USERS_COUNT):
        TEST_USER(i+1)
    return


@pytest.mark.django_db
class TestCustomUserViewSet():
    """Производит тест вью-сета "CustomUserViewSet"."""

    VALID_POST_DATA = {
        'email': f'{"1"*(USER_EMAIL_MAX_LEN-len("@email.com"))}@email.com',
        'username': f'{"1"*USER_USERNAME_MAX_LEN}',
        'first_name': f'{"1"*USER_FIRST_NAME_MAX_LEN}',
        'last_name': f'{"1"*USER_SECOND_NAME_MAX_LEN}',
        'password': f'{"1"*USER_PASSWORD_MAX_LEN}'}
    VALID_POST_DATA_EXP = {
        'email': f'{"1"*(USER_EMAIL_MAX_LEN-len("@email.com"))}@email.com',
        'id': 1,
        'username': f'{"1"*USER_USERNAME_MAX_LEN}',
        'first_name': f'{"1"*USER_FIRST_NAME_MAX_LEN}',
        'last_name': f'{"1"*USER_SECOND_NAME_MAX_LEN}',
        'is_subscribed': False}
    NON_VALID_POST_DATA_LENGTH = {
        'email': f'{"1"*(USER_EMAIL_MAX_LEN-len("@email.com")+1)}@email.com',
        'username': f'{"1"*(USER_USERNAME_MAX_LEN+1)}',
        'first_name': f'{"1"*(USER_FIRST_NAME_MAX_LEN+1)}',
        'last_name': f'{"1"*(USER_SECOND_NAME_MAX_LEN+1)}',
        'password': f'{"1"*(USER_PASSWORD_MAX_LEN+1)}'}
    NON_VALID_POST_DATA_LENGTH_EXP = {
        'email': [
            'Убедитесь, что это значение содержит не более 254 символов.'],
        'username': [
            'Убедитесь, что это значение содержит не более 150 символов.'],
        'first_name': [
            'Убедитесь, что это значение содержит не более 150 символов.'],
        'last_name': [
            'Убедитесь, что это значение содержит не более 150 символов.'],
        'password': [
            'Убедитесь, что это значение содержит не более 150 символов.']}
    NON_VALID_POST_DATA_EMPTY = {}
    NON_VALID_POST_DATA_EMPTY_EXP = {
        'email': ['Обязательное поле.'],
        'username': ['Обязательное поле.'],
        'first_name': ['Обязательное поле.'],
        'last_name': ['Обязательное поле.'],
        'password': ['Обязательное поле.']}
    NON_VALID_POST_DATA_EMAIL = {
        'email': 'None',
        'username': 'test_username',
        'first_name': 'test_first_name',
        'last_name': 'test_last_name',
        'password': 'test_username'}
    NON_VALID_POST_DATA_EMAIL_EXP = {
        'email': ['Введите правильный адрес электронной почты.']}
    NON_VALID_POST_DATA_USERNAME = {
        'email': 'test@email.com',
        'username': '12345!!!😊',
        'first_name': 'test_first_name',
        'last_name': 'test_last_name',
        'password': 'test_password'}
    NON_VALID_POST_DATA_USERNAME_EXP = {
        'username': [
            'Использование "!", "1", "2", "3", "4", "5", "😊" в имени '
            'пользователя запрещено.']}
    NON_VALID_POST_DATA_EXISTED = {
        'email': 'test_user_1@email.com',
        'username': 'test_user_1',
        'first_name': 'test_user_1_first_name',
        'last_name': 'test_user_1_last_name',
        'password': 'test_user_1_password'}
    NON_VALID_POST_DATA_EXISTED_EXP = {
        'email': ['Пользователь с такой электронной почтой уже существует.'],
        'username': ['Пользователь с таким именем уже существует.']}

    def auth_client(self) -> APIClient:
        """Возвращает объект авторизированного клиента.
        Авторизация производится форсированная: без использования токенов."""
        auth_client = APIClient()
        auth_client.force_authenticate(user=None)
        return auth_client

    def anon_client(self) -> APIClient:
        """Возвращает объект анонимного клиента."""
        return APIClient()

    def users_get(self, client) -> None:
        """Совершает GET-запрос к списку пользователей по эндпоинту
        "/api/v1/users/" от лица переданного клиента.
        Проверяет ответ на соответствие ожидаемым данным
        (не зависят от статуса клиента)."""
        response = client.get(USERS_URL)
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert len(data) == TEST_USERS_COUNT
        expected_data = [
            {'email': 'test_user_1@email.com',
             'id': 1,
             'username': 'test_user_1',
             'first_name': 'test_user_1_first_name',
             'last_name': 'test_user_1_last_name',
             'is_subscribed': False},
            {'email': 'test_user_2@email.com',
             'id': 2,
             'username': 'test_user_2',
             'first_name': 'test_user_2_first_name',
             'last_name': 'test_user_2_last_name',
             'is_subscribed': False},
            {'email': 'test_user_3@email.com',
             'id': 3,
             'username': 'test_user_3',
             'first_name': 'test_user_3_first_name',
             'last_name': 'test_user_3_last_name',
             'is_subscribed': False}]
        assert data == expected_data
        return

    def users_post(
            self,
            client: APIClient,
            data: dict[str, any],
            expected_data: dict[str, any],
            expected_status: status,
            expected_users_count: int) -> None:
        """Совершает POST-запрос к списку пользователей по эндпоинту
        "/api/v1/users/" от лица переданного клиента."""
        response = client.post(
            USERS_URL, json.dumps(data), content_type='application/json')
        assert response.status_code == expected_status
        assert User.objects.all().count() == expected_users_count
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_delete_not_allowed(self, client_func):
        """Тест DELETE-запроса на удаление пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func(self)
        response = client.delete(
            USERS_URL, json.dumps({}), content_type='application/json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_get(self, client_func, create_users) -> None:
        """Тест GET-запроса списка пользователей по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями."""
        self.users_get(client=client_func(self))
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_patch_not_allowed(self, client_func) -> None:
        """Тест PATCH-запроса на обновления пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func(self)
        response = client.patch(
            USERS_URL, json.dumps({}), content_type='application/json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_post_allow_create(self, client_func) -> None:
        """Тест POST-запроса на создание нового пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Передаваемые данные являются заведомо валидными."""
        self.users_post(
            client=client_func(self),
            data=self.VALID_POST_DATA,
            expected_data=self.VALID_POST_DATA_EXP,
            expected_status=status.HTTP_201_CREATED,
            expected_users_count=1)
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('data, expected_data', [
        (NON_VALID_POST_DATA_EMPTY, NON_VALID_POST_DATA_EMPTY_EXP),
        (NON_VALID_POST_DATA_LENGTH, NON_VALID_POST_DATA_LENGTH_EXP),
        (NON_VALID_POST_DATA_EMAIL, NON_VALID_POST_DATA_EMAIL_EXP),
        (NON_VALID_POST_DATA_USERNAME, NON_VALID_POST_DATA_USERNAME_EXP),
        (NON_VALID_POST_DATA_EXISTED, NON_VALID_POST_DATA_EXISTED_EXP)])
    def test_users_post_field_validation(
            self, client_func, data, expected_data, create_users) -> None:
        """Тест POST-запроса на создание нового пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Передаваемые данные являются заведомо не валидными валидными."""
        self.users_post(
            client=client_func(self),
            data=data,
            expected_data=expected_data,
            expected_status=status.HTTP_400_BAD_REQUEST,
            expected_users_count=TEST_USERS_COUNT)
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_put_not_allowed(self, client_func) -> None:
        """Тест PUT-запроса на замену пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func(self)
        response = client.put(
            USERS_URL, json.dumps({}), content_type='application/json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return
