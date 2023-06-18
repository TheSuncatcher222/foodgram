import json

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from api.v1.serializers import (
    USER_EMAIL_MAX_LEN, USER_FIRST_NAME_MAX_LEN, USER_PASSWORD_MAX_LEN,
    USER_SECOND_NAME_MAX_LEN, USER_USERNAME_MAX_LEN)
from footgram_app.models import Subscriptions
from footgram_app.tests.test_models import create_user_obj

URL_AUTH: str = '/api/v1/auth/token/'
URL_AUTH_LOGIN: str = f'{URL_AUTH}login/'
URL_AUTH_LOGOUT: str = f'{URL_AUTH}logout/'
URL_USERS: str = '/api/v1/users/'
URL_USERS_ME: str = f'{URL_USERS}me/'
URL_USERS_SET_PASSWORD: str = f'{URL_USERS}set_password/'

TEST_USERS_COUNT: int = 3


def anon_client() -> APIClient:
    """Возвращает объект анонимного клиента."""
    return APIClient()


def auth_client() -> APIClient:
    """Возвращает объект авторизированного клиента.
    Авторизация производится форсированная: без использования токенов."""
    auth_client = APIClient()
    auth_client.force_authenticate(user=None)
    return auth_client


@pytest.fixture()
def create_users() -> None:
    """Фикстура для наполнения БД заданным числом пользователей."""
    for i in range(1, TEST_USERS_COUNT+1):
        create_user_obj(num=i)
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
        'email': 'test_user_email_1@email.com',
        'username': 'test_user_username_1',
        'first_name': 'test_user_first_name_1',
        'last_name': 'test_user_last_name_1',
        'password': 'test_user_password_1'}
    NON_VALID_POST_DATA_EXISTED_EXP = {
        'email': ['Пользователь с такой электронной почтой уже существует.'],
        'username': ['Пользователь с таким именем уже существует.']}

    def users_get(self, client: APIClient) -> dict:
        """Совершает GET-запрос к списку пользователей по эндпоинту
        "/api/v1/users/" от лица переданного клиента.
        В случае успешного запроса возвращает ответ, приведенный к формату
        данных Python."""
        response = client.get(URL_USERS)
        assert response.status_code == status.HTTP_200_OK
        return json.loads(response.content)

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
            URL_USERS, json.dumps(data), content_type='application/json')
        assert response.status_code == expected_status
        assert User.objects.all().count() == expected_users_count
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_delete_not_allowed(self, client_func):
        """Тест DELETE-запроса на удаление пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func()
        response = client.delete(
            URL_USERS, json.dumps({}), content_type='application/json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_get(self, client_func, create_users) -> None:
        """Тест GET-запроса списка пользователей по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями.
        В классе используется пагинация. В рамках теста производится анализ
        содержимого "results". Тест непосредственно пагинации производится
        в другой функции."""
        expected_data: dict[str, any] = [
            {'email': 'test_user_email_1@email.com',
             'id': 1,
             'username': 'test_user_username_1',
             'first_name': 'test_user_first_name_1',
             'last_name': 'test_user_last_name_1',
             'is_subscribed': False},
            {'email': 'test_user_email_2@email.com',
             'id': 2,
             'username': 'test_user_username_2',
             'first_name': 'test_user_first_name_2',
             'last_name': 'test_user_last_name_2',
             'is_subscribed': False},
            {'email': 'test_user_email_3@email.com',
             'id': 3,
             'username': 'test_user_username_3',
             'first_name': 'test_user_first_name_3',
             'last_name': 'test_user_last_name_3',
             'is_subscribed': False}]
        data: dict = self.users_get(client=client_func())
        results_pagination: dict = data['results']
        assert len(results_pagination) == TEST_USERS_COUNT
        assert results_pagination == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_patch_not_allowed(self, client_func) -> None:
        """Тест PATCH-запроса на обновления пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func()
        response = client.patch(
            URL_USERS, json.dumps({}), content_type='application/json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_post_allow_create(self, client_func) -> None:
        """Тест POST-запроса на создание нового пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Передаваемые данные являются заведомо валидными."""
        self.users_post(
            client=client_func(),
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
            client=client_func(),
            data=data,
            expected_data=expected_data,
            expected_status=status.HTTP_400_BAD_REQUEST,
            expected_users_count=TEST_USERS_COUNT)
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_put_not_allowed(self, client_func) -> None:
        """Тест PUT-запроса на замену пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func()
        response = client.put(
            URL_USERS, json.dumps({}), content_type='application/json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_pk(self, client_func: any, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/{pk}/" для анонимного и авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями."""
        client = client_func()
        response = client.get(f'{URL_USERS}1/')
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == {
            'email': 'test_user_email_1@email.com',
            'id': 1,
            'username': 'test_user_username_1',
            'first_name': 'test_user_first_name_1',
            'last_name': 'test_user_last_name_1',
            'is_subscribed': False}
        return

    def test_users_pk_subscription(self, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/{pk}/" для авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями.
        Моделируется подписка клиента на другого пользователя."""
        subscriber: User = User.objects.get(id=1)
        subscription_to: User = User.objects.get(id=2)
        Subscriptions.objects.create(
            subscriber=subscriber,
            subscription_to=subscription_to)
        client = auth_client()
        client.force_authenticate(user=subscriber)
        response = client.get(f'{URL_USERS}2/')
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == {
            'email': 'test_user_email_2@email.com',
            'id': 2,
            'username': 'test_user_username_2',
            'first_name': 'test_user_first_name_2',
            'last_name': 'test_user_last_name_2',
            'is_subscribed': True}
        return

    def test_users_me_anon(self, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/me/" для анонимного клиента."""
        client: APIClient = anon_client()
        response = client.get(URL_USERS_ME)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data: dict = json.loads(response.content)
        assert data == {'detail': 'Учетные данные не были предоставлены.'}
        return

    def test_users_me_auth(self, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/me/" для авторизированного клиента."""
        test_user: User = User.objects.get(id=1)
        client = APIClient()
        client.force_authenticate(user=test_user)
        response = client.get(URL_USERS_ME)
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == {
            'email': 'test_user_email_1@email.com',
            'id': 1,
            'username': 'test_user_username_1',
            'first_name': 'test_user_first_name_1',
            'last_name': 'test_user_last_name_1',
            'is_subscribed': False}

    @pytest.mark.parametrize(
        'token, expected_data',
        [(' ', {'detail':
                'Недопустимый заголовок токена. '
                'Не предоставлены учетные данные.'}),
         ('100%_non_valid_token', {'detail': 'Недопустимый токен.'})])
    def test_users_me_invalid_token(
            self, token: str, expected_data: dict, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/me/" для клиента с поврежденным токеном авторизации."""
        client: APIClient = anon_client()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = client.get(URL_USERS_ME)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

    # ToDo: разобраться, почему возникает ошибка в response:
    # {'current_password': ['Неправильный пароль.']}

    # def test_users_set_password(self):
    #     """Тест POST-запроса на страницу изменения пароля по эндпоинту
    #     "/api/users/set_password/" для авторизованного клиента."""
    #     TEST_PASSWORD_NEW: str = '31fdss2311sddad213'
    #     test_user = User.objects.create(
    #         username='test_user',
    #         password='dasd3213123')
    #     token, _ = Token.objects.get_or_create(user=test_user)
    #     client = APIClient()
    #     client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    #     data: dict = {
    #         'current_password': test_user.password,
    #         'new_password': TEST_PASSWORD_NEW}
    #     response = client.post(
    #         URL_USERS_SET_PASSWORD,
    #         json.dumps(data),
    #         content_type='application/json')
    #     content = json.loads(response.content)
    #     assert content == None

    # ToDo: разобраться, почему возникает ошибка в response:
    # {'non_field_errors':
    # ['Невозможно войти с предоставленными учетными данными.']}

    # def test_users_get_token(self, create_users):
    #     """Тест POST-запроса на страницу получения токена по эндпоинту
    #     "/api/auth/token/login/" для анонимного клиента."""
    #     test_user: User = User.objects.get(id=1)
    #     client = anon_client()
    #     data: dict = {
    #         'email': test_user.email,
    #         'password': 'test_password_1'}
    #     response = client.post(
    #         URL_AUTH_LOGIN,
    #         json.dumps(data),
    #         content_type='application/json')
    #     assert response.status_code == status.HTTP_200_OK
    #     content = json.loads(response.content)
    #     assert content == 1
    #     assert isinstance(content['auth_token'], str)
    #     assert len(content['auth_token'] > 0)
