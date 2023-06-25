import json
import os

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from pathlib import Path
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from api.v1.serializers import (
    USER_EMAIL_MAX_LEN, USER_FIRST_NAME_MAX_LEN, USER_PASSWORD_MAX_LEN,
    USER_SECOND_NAME_MAX_LEN, USER_USERNAME_MAX_LEN)
from footgram_app.models import (
    RECIPES_MEDIA_ROOT,
    Ingredients, Recipes, Subscriptions, Tags)
from footgram_app.tests.test_models import (
    create_ingredient_obj, create_recipe_ingredient_obj, create_recipe_obj,
    create_recipe_tag_obj, create_shopping_cart_obj, create_tag_obj,
    create_user_obj, create_user_obj_with_hash)

URL_API_V1: str = '/api/v1/'
URL_AUTH: str = f'{URL_API_V1}auth/token/'
URL_AUTH_LOGIN: str = f'{URL_AUTH}login/'
URL_AUTH_LOGOUT: str = f'{URL_AUTH}logout/'
URL_INGREDIENTS: str = f'{URL_API_V1}ingredients/'
URL_INGREDIENTS_PK: str = URL_INGREDIENTS + '{pk}/'
URL_RECIPES: str = f'{URL_API_V1}recipes/'
URL_RECIPES_PK: str = URL_RECIPES + '{pk}/'
URL_RECIPES_FAVORITE: str = f'{URL_RECIPES_PK}favorite/'
URL_TAGS: str = f'{URL_API_V1}tags/'
URL_TAGS_PK: str = URL_TAGS + '{pk}/'
URL_SHOPPING_LIST: str = f'{URL_RECIPES}download_shopping_cart/'
URL_SHOPPING_UPDATE: str = f'{URL_RECIPES_PK}shopping_cart/'
URL_USERS: str = f'{URL_API_V1}users/'
URL_USERS_PK: str = URL_USERS + '{pk}/'
URL_USERS_ME: str = f'{URL_USERS}me/'
URL_USERS_SET_PASSWORD: str = f'{URL_USERS}set_password/'
URL_USERS_SUBSCRIPTION_UPDATE: str = f'{URL_USERS_PK}subscribe/'
URL_USERS_SUBSCRIPTIONS: str = f'{URL_USERS}subscriptions/'

"""Количество объектов моделей (Models), должны создавать все фикстуры."""
TEST_FIXTURES_OBJ_AMOUNT: int = 3


def anon_client() -> APIClient:
    """Возвращает объект анонимного клиента."""
    return APIClient()


def auth_client() -> APIClient:
    """Возвращает объект авторизированного клиента.
    Авторизация производится форсированная: без использования токенов."""
    auth_client = APIClient()
    auth_client.force_authenticate(user=None)
    return auth_client


def auth_token_client(user_id: int = 1) -> APIClient:
    """Возвращает объект авторизированного клиента c токеном.
    Токен записывается в заголовок запросов и применяется автоматически.
    Токен формируется для переданного экземпляра модели "Users".
    По-умолчанию берется пользователь с id=1."""
    token_user: User = User.objects.get(id=user_id)
    token, _ = Token.objects.get_or_create(user=token_user)
    auth_token_client: APIClient = anon_client()
    auth_token_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return auth_token_client


@pytest.fixture()
def create_ingredients() -> None:
    """Фикстура для наполнения БД заданным числом ингредиентов."""
    for i in range(1, TEST_FIXTURES_OBJ_AMOUNT+1):
        create_ingredient_obj(num=i)
    return


@pytest.fixture()
def create_recipes_users() -> None:
    """Фикстура для наполнения БД заданным числом рецептов.
    Также создает пользователей, которые являются авторами этих рецептов."""
    for i in range(1, TEST_FIXTURES_OBJ_AMOUNT+1):
        user: User = create_user_obj(num=i)
        create_recipe_obj(num=i, user=user)
    return


@pytest.fixture()
def create_recipes_ingredients_tags_users() -> None:
    """Фикстура для наполнения БД заданным числом рецептов.
    Также создает дополнительные объекты:
        - ингредиенты;
        - пользователей;
        - теги.
    Затем объекты связываются с рецептами согласно правилам полей "Recipes".
    """
    for i in range(1, TEST_FIXTURES_OBJ_AMOUNT+1):
        user: User = create_user_obj(num=i)
        recipe: Recipes = create_recipe_obj(num=i, user=user)
        tag: Tags = create_tag_obj(num=i)
        create_recipe_tag_obj(recipe=recipe, tag=tag)
        ingredient: Ingredients = create_ingredient_obj(num=i)
        create_recipe_ingredient_obj(
            amount=i, ingredient=ingredient, recipe=recipe)
    return


@pytest.fixture()
def create_tags() -> None:
    """Фикстура для наполнения БД заданным числом пользователей."""
    for i in range(1, TEST_FIXTURES_OBJ_AMOUNT+1):
        create_tag_obj(num=i)
    return


@pytest.fixture()
def create_users() -> None:
    """Фикстура для наполнения БД заданным числом пользователей."""
    for i in range(1, TEST_FIXTURES_OBJ_AMOUNT+1):
        create_user_obj(num=i)
    return


# ToDo: заменить в тестах "== status" на "== status_code"


@pytest.mark.django_db
class TestAuth():
    """Производит тест корректности настройки авторизации Djoser."""

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_login_post(self, client_func) -> None:
        """Тест POST-запроса на страницу получения токена по эндпоинту
        "/api/auth/token/login/" для анонимного и авторизованного клиента."""
        test_user: User = create_user_obj_with_hash(num=1)
        token, _ = Token.objects.get_or_create(user=test_user)
        client: APIClient = client_func()
        data: dict = {
            'username': 'test_user_username_1',
            'password': 'test_user_password_1'}
        response = client.post(
            URL_AUTH_LOGIN,
            json.dumps(data),
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == {'auth_token': token.key}
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'get', 'patch', 'put'])
    def test_users_login_not_allowed(self, client_func, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/auth/token/login/":
            - DELETE;
            - GET;
            - PATCH;
            - PUT."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_AUTH_LOGIN)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    def test_users_logout_post(self) -> None:
        """Тест POST-запроса на страницу удаления токена по эндпоинту
        "/api/auth/token/logout/" для анонимного и авторизованного клиента."""
        test_user: User = create_user_obj_with_hash(num=1)
        assert not Token.objects.filter(user=test_user).exists()
        token, _ = Token.objects.get_or_create(user=test_user)
        assert Token.objects.filter(user=test_user).exists()
        client: APIClient = anon_client()
        response = client.post(URL_AUTH_LOGOUT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Token.objects.filter(user=test_user).exists()
        client: APIClient = auth_token_client(user_id=1)
        response = client.post(URL_AUTH_LOGOUT)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Token.objects.filter(user=test_user).exists()
        return

    @pytest.mark.parametrize('method', ['delete', 'get', 'patch', 'put'])
    def test_users_logout_not_allowed(self, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/auth/token/logout/":
            - DELETE;
            - GET;
            - PATCH;
            - PUT."""
        client: APIClient = anon_client()
        response = getattr(client, method)(URL_AUTH_LOGOUT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        create_user_obj_with_hash(num=1)
        client: APIClient = auth_token_client(user_id=1)
        response = getattr(client, method)(URL_AUTH_LOGOUT)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return


@pytest.mark.django_db
class TestCustomUserViewSet():
    """Производит тест вью-сета "CustomUserViewSet"."""

    VALID_POST_DATA: dict = {
        'email': f'{"1"*(USER_EMAIL_MAX_LEN-len("@email.com"))}@email.com',
        'username': f'{"1"*USER_USERNAME_MAX_LEN}',
        'first_name': f'{"1"*USER_FIRST_NAME_MAX_LEN}',
        'last_name': f'{"1"*USER_SECOND_NAME_MAX_LEN}',
        'password': f'{"1"*USER_PASSWORD_MAX_LEN}'}
    VALID_POST_DATA_EXP: dict = {
        'email': f'{"1"*(USER_EMAIL_MAX_LEN-len("@email.com"))}@email.com',
        'id': 1,
        'username': f'{"1"*USER_USERNAME_MAX_LEN}',
        'first_name': f'{"1"*USER_FIRST_NAME_MAX_LEN}',
        'last_name': f'{"1"*USER_SECOND_NAME_MAX_LEN}',
        'is_subscribed': False}
    NON_VALID_POST_DATA_LENGTH: dict = {
        'email': f'{"1"*(USER_EMAIL_MAX_LEN-len("@email.com")+1)}@email.com',
        'username': f'{"1"*(USER_USERNAME_MAX_LEN+1)}',
        'first_name': f'{"1"*(USER_FIRST_NAME_MAX_LEN+1)}',
        'last_name': f'{"1"*(USER_SECOND_NAME_MAX_LEN+1)}',
        'password': f'{"1"*(USER_PASSWORD_MAX_LEN+1)}'}
    NON_VALID_POST_DATA_LENGTH_EXP: dict = {
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
    NON_VALID_POST_DATA_EMPTY: dict = {}
    NON_VALID_POST_DATA_EMPTY_EXP: dict = {
        'email': ['Обязательное поле.'],
        'username': ['Обязательное поле.'],
        'first_name': ['Обязательное поле.'],
        'last_name': ['Обязательное поле.'],
        'password': ['Обязательное поле.']}
    NON_VALID_POST_DATA_EMAIL: dict = {
        'email': 'None',
        'username': 'test_username',
        'first_name': 'test_first_name',
        'last_name': 'test_last_name',
        'password': 'test_username'}
    NON_VALID_POST_DATA_EMAIL_EXP: dict = {
        'email': ['Введите правильный адрес электронной почты.']}
    NON_VALID_POST_DATA_USERNAME: dict = {
        'email': 'test@email.com',
        'username': '12345!!!😊',
        'first_name': 'test_first_name',
        'last_name': 'test_last_name',
        'password': 'test_password'}
    NON_VALID_POST_DATA_USERNAME_EXP: dict = {
        'username': [
            'Использование "!", "1", "2", "3", "4", "5", "😊" в имени '
            'пользователя запрещено.']}
    NON_VALID_POST_DATA_EXISTED: dict = {
        'email': 'test_user_email_1@email.com',
        'username': 'test_user_username_1',
        'first_name': 'test_user_first_name_1',
        'last_name': 'test_user_last_name_1',
        'password': 'test_user_password_1'}
    NON_VALID_POST_DATA_EXISTED_EXP: dict = {
        'email': ['Пользователь с такой электронной почтой уже существует.'],
        'username': ['Пользователь с таким именем уже существует.']}

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_get(self, client_func, create_users) -> None:
        """Тест GET-запроса списка пользователей по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями.
        В классе используется пагинация. В рамках теста производится анализ
        содержимого "results" для первого элемента. Тест непосредственно
        пагинации производится в функции "test_view_sets_pagination"."""
        expected_data: dict[str, any] = {
            'email': 'test_user_email_1@email.com',
            'id': 1,
            'username': 'test_user_username_1',
            'first_name': 'test_user_first_name_1',
            'last_name': 'test_user_last_name_1',
            'is_subscribed': False}
        client: APIClient = client_func()
        response = client.get(URL_USERS)
        assert response.status_code == status.HTTP_200_OK
        results_pagination: dict = json.loads(response.content)['results']
        assert len(results_pagination) == TEST_FIXTURES_OBJ_AMOUNT
        assert results_pagination[0] == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_post(self, client_func) -> None:
        """Тест POST-запроса на создание нового пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Передаваемые данные являются заведомо валидными."""
        client: APIClient = client_func()
        assert User.objects.all().count() == 0
        response = client.post(
            URL_USERS,
            json.dumps(self.VALID_POST_DATA),
            content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.all().count() == 1
        data: dict = json.loads(response.content)
        assert data == self.VALID_POST_DATA_EXP
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('data, expected_data', [
        (NON_VALID_POST_DATA_EMPTY, NON_VALID_POST_DATA_EMPTY_EXP),
        (NON_VALID_POST_DATA_LENGTH, NON_VALID_POST_DATA_LENGTH_EXP),
        (NON_VALID_POST_DATA_EMAIL, NON_VALID_POST_DATA_EMAIL_EXP),
        (NON_VALID_POST_DATA_USERNAME, NON_VALID_POST_DATA_USERNAME_EXP),
        (NON_VALID_POST_DATA_EXISTED, NON_VALID_POST_DATA_EXISTED_EXP)])
    def test_users_post_invalid_data(
            self,
            client_func,
            data: dict,
            expected_data: dict,
            create_users) -> None:
        """Тест POST-запроса на создание нового пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Передаваемые данные являются заведомо не валидными."""
        client: APIClient = client_func()
        assert User.objects.all().count() == TEST_FIXTURES_OBJ_AMOUNT
        response = client.post(
            URL_USERS,
            json.dumps(data),
            content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.all().count() == TEST_FIXTURES_OBJ_AMOUNT
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'put'])
    def test_users_not_allowed(
            self, client_func, method: str, create_users) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/users/{pk}/":
            - DELETE;
            - PATCH;
            - PUT.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_USERS_PK.format(pk=1))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize(
        'client_func, status_code, expected_data',
        [(anon_client,
          status.HTTP_401_UNAUTHORIZED,
          {'detail': 'Учетные данные не были предоставлены.'}),
         (auth_token_client,
          status.HTTP_200_OK,
          {'email': 'test_user_email_1@email.com',
           'id': 1,
           'username': 'test_user_username_1',
           'first_name': 'test_user_first_name_1',
           'last_name': 'test_user_last_name_1',
           'is_subscribed': False})])
    def test_users_me_get(
            self,
            client_func,
            status_code: status,
            expected_data: dict,
            create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/me/" для анонимного и авторизированного клиента."""
        client: APIClient = client_func()
        response = client.get(URL_USERS_ME)
        assert response.status_code == status_code
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

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

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'post', 'put'])
    def test_users_me_not_allowed(
            self, client_func, method: str, create_users) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/users/me/":
            - DELETE;
            - PATCH;
            - POST;
            - PUT.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_USERS_PK.format(pk=1))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_pk_get(self, client_func, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/{pk}/" для анонимного и авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями."""
        client: APIClient = client_func()
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

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'post', 'put'])
    def test_users_pk_not_allowed(
            self, client_func, method: str, create_users) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/users/{pk}/":
            - DELETE;
            - PATCH;
            - POST;
            - PUT.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями."""
        client: APIClient = client_func()
        response = getattr(client, method)(f'{URL_USERS}1/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize(
        'to_user_id, status_code, expected_data',
        [(1,
          status.HTTP_400_BAD_REQUEST,
          {'non_field_errors':
           ['Вы не можете подписаться на себя.']}),
         (2,
          status.HTTP_400_BAD_REQUEST,
          {'non_field_errors':
           ['Вы уже подписаны на пользователя test_user_username_2.']}),
         (3,
          status.HTTP_201_CREATED,
          {'email': 'test_user_email_3@email.com',
           'id': 3,
           'username': 'test_user_username_3',
           'first_name': 'test_user_first_name_3',
           'last_name': 'test_user_last_name_3',
           'is_subscribed': True,
           'recipes_count': 0,
           'recipes': []}),
         (4,
          status.HTTP_404_NOT_FOUND,
          {'detail':
           'Страница не найдена.'})])
    def test_users_pk_subscribe_post(
            self,
            to_user_id: int,
            status_code: status,
            expected_data: dict,
            create_users) -> None:
        """Тест POST-запроса на подписку на пользователя по эндпоинту
        "/api/v1/users/{pk}/subscribe" авторизированного клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями.
        Моделируется подписка клиента на другого пользователя.
        В тесте создается подписка пользователя 1 на пользователя 2
        и рассматриваются следующие возможные случаи:
            1) пользователь 1 подписывается сам на себя;
            2) пользователь 1 подписывается на пользователя 2 повторно;
            3) пользователь 1 подписывается на пользователя 3;
            4) пользователь 1 подписывается несуществующего пользователя."""
        USER_ID: int = 1
        TO_SUBSCRIBE_USER: int = 2
        subscriber: User = User.objects.get(id=USER_ID)
        subscription_to: User = User.objects.get(id=TO_SUBSCRIBE_USER)
        Subscriptions.objects.create(
            subscriber=subscriber,
            subscription_to=subscription_to)
        client: APIClient = anon_client()
        response = client.post(
            f'{URL_USERS_SUBSCRIPTION_UPDATE.format(pk=to_user_id)}')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        client: APIClient = auth_token_client(user_id=USER_ID)
        response = client.post(
            f'{URL_USERS_SUBSCRIPTION_UPDATE.format(pk=to_user_id)}')
        assert response.status_code == status_code
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

    @pytest.mark.parametrize('to_user_id, status_code, expected_data', [
        (2,
         status.HTTP_204_NO_CONTENT,
         {}),
        (3,
         status.HTTP_400_BAD_REQUEST,
         {'non_field_errors':
          ['Вы не были подписаны на пользователя test_user_username_3.']}),
        (4,
         status.HTTP_404_NOT_FOUND,
         {'detail':
          'Страница не найдена.'})])
    def test_users_pk_subscribe_delete(
            self,
            to_user_id: int,
            status_code: status,
            expected_data: dict,
            create_users) -> None:
        """Тест DELETE-запроса на удаление подписки на пользователя по
        эндпоинту "/api/v1/users/{pk}/subscribe/".
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями.
        В тесте создается подписка пользователя 1 на пользователя 2
        и рассматриваются следующие возможные случаи:
            1) пользователь 1 отписывается от существующей подписки;
            2) пользователь 1 отписывается от несуществующей подписки;
            3) пользователь 1 отписывается от несуществующего пользователя."""
        USER_ID: int = 1
        TO_SUBSCRIBE_USER: int = 2
        test_user: User = User.objects.get(id=USER_ID)
        already_subscribed: User = User.objects.get(id=TO_SUBSCRIBE_USER)
        Subscriptions.objects.create(
            subscriber=test_user,
            subscription_to=already_subscribed)
        client: APIClient = anon_client()
        response = client.post(
            f'{URL_USERS_SUBSCRIPTION_UPDATE.format(pk=to_user_id)}')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        client: APIClient = auth_token_client(user_id=USER_ID)
        response = client.delete(
            f'{URL_USERS_SUBSCRIPTION_UPDATE.format(pk=to_user_id)}')
        assert response.status_code == status_code
        try:
            data: dict = json.loads(response.content)
        except json.decoder.JSONDecodeError:
            """При статусе 204 возвращается ответ без контента."""
            data: dict = {}
        assert data == expected_data
        return

    @pytest.mark.parametrize('method', ['get', 'patch', 'put'])
    def test_users_pk_subscribe_not_allowed(self, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту
        "/api/v1/users/{pk}/subscribe/":
            - GET;
            - PATCH;
            - PUT."""
        client: APIClient = anon_client()
        response = getattr(client, method)(URL_USERS_SET_PASSWORD)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        create_user_obj_with_hash(num=1)
        client: APIClient = auth_token_client(user_id=1)
        response = getattr(client, method)(URL_USERS_SET_PASSWORD)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_users_pk_subscription_get(self, create_users) -> None:
        """Тест GET-запроса на личную страницу пользователя по эндпоинту
        "/api/v1/users/{pk}/subscribe/" для анонимного и авторизированного
        клиента.
        Используется фикстура "create_users" для наполнения тестовой
        БД пользователями.
        В классе используется пагинация. В рамках теста производится анализ
        содержимого "results" для первого элемента. Тест непосредственно
        пагинации производится в функции "test_view_sets_pagination".
        В тесте создается подписка пользователя 1 на пользователя 2."""
        USER_ID: int = 1
        TO_SUBSCRIBE_USER: int = 2
        subscriber: User = User.objects.get(id=USER_ID)
        subscription_to: User = User.objects.get(id=TO_SUBSCRIBE_USER)
        Subscriptions.objects.create(
            subscriber=subscriber,
            subscription_to=subscription_to)
        client: APIClient = anon_client()
        response = client.get(URL_USERS_SUBSCRIPTIONS)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        client: APIClient = auth_token_client(user_id=USER_ID)
        response = client.get(URL_USERS_SUBSCRIPTIONS)
        assert response.status_code == status.HTTP_200_OK
        results_pagination: dict = json.loads(response.content)['results']
        assert len(results_pagination) == 1
        assert results_pagination[0] == {
            'email': 'test_user_email_2@email.com',
            'id': 2,
            'username': 'test_user_username_2',
            'first_name': 'test_user_first_name_2',
            'last_name': 'test_user_last_name_2',
            'is_subscribed': True,
            'recipes_count': 0,
            'recipes': []}
        return

    @pytest.mark.parametrize('method', ['delete', 'patch', 'post', 'put'])
    def test_users_pk_subscription_not_allowed(self, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту
        "/api/v1/users/{pk}/subscribe/":
            - GET;
            - PATCH;
            - PUT."""
        client: APIClient = anon_client()
        response = getattr(client, method)(URL_USERS_SUBSCRIPTIONS)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        create_user_obj_with_hash(num=1)
        client: APIClient = auth_token_client(user_id=1)
        response = getattr(client, method)(URL_USERS_SUBSCRIPTIONS)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.parametrize(
        'client_func, status',
        [(anon_client, status.HTTP_401_UNAUTHORIZED),
         (auth_token_client, status.HTTP_204_NO_CONTENT)])
    def test_users_set_password_post(self, client_func, status) -> None:
        """Тест POST-запроса на страницу изменения пароля по эндпоинту
        "/api/users/set_password/" для авторизованного клиента."""
        create_user_obj_with_hash(num=1)
        client: APIClient = client_func()
        NEW_PASSWORD: str = 'some_new_data_pass'
        data: dict = {
            'current_password': 'test_user_password_1',
            'new_password': NEW_PASSWORD}
        response = client.post(
            URL_USERS_SET_PASSWORD,
            json.dumps(data),
            content_type='application/json')
        assert response.status_code == status

    @pytest.mark.parametrize('method', ['delete', 'get', 'patch', 'put'])
    def test_users_set_password_not_allowed(self, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/users/set_password/":
            - DELETE;
            - GET;
            - PATCH;
            - PUT."""
        client: APIClient = anon_client()
        response = getattr(client, method)(URL_USERS_SET_PASSWORD)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        create_user_obj_with_hash(num=1)
        client: APIClient = auth_token_client(user_id=1)
        response = getattr(client, method)(URL_USERS_SET_PASSWORD)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestIngredientsViewSet():
    """Производит тест вью-сета "IngredientsViewSet"."""

    FIRST_INGREDIENT_EXP: dict = {
        'id': 1,
        'name': 'test_ingredient_name_1',
        'measurement_unit': 'батон'}

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_ingredients_get(self, client_func, create_ingredients) -> None:
        """Тест GET-запроса списка ингредиентов по эндпоинту
        "/api/v1/ingredients/" для анонимного и авторизированного клиента.
        Используется фикстура "create_ingredients" для наполнения
        тестовой БД ингредиентами.
        В классе используется пагинация. В рамках теста производится анализ
        содержимого "results" для первого элемента. Тест непосредственно
        пагинации производится в функции "test_view_sets_pagination"."""
        client: APIClient = client_func()
        response = client.get(URL_INGREDIENTS)
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        results_pagination: dict = data['results']
        assert results_pagination[0] == self.FIRST_INGREDIENT_EXP
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'post', 'put'])
    def test_ingredients_not_allowed(
            self, client_func, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/ingredients/":
            - DELETE;
            - PATCH;
            - POST;
            - PUT."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_INGREDIENTS)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_ingredients_pk_get(
            self, client_func, create_ingredients) -> None:
        """Тест GET-запроса на ингредиент по эндпоинту
        "/api/v1/ingredients/{pk}/" для анонимного и авторизированного клиента.
        Используется фикстура "create_ingredients" для наполнения
        тестовой БД ингредиентами."""
        client: APIClient = client_func()
        response = client.get(URL_INGREDIENTS_PK.format(pk=1))
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == self.FIRST_INGREDIENT_EXP
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'post', 'put'])
    def test_ingredients_pk_not_allowed(
            self, client_func, method: str, create_ingredients) -> None:
        """Тест запрета на CRUD запросы к эндпоинту
        "/api/v1/ingredients/{pk}/":
            - DELETE;
            - PATCH;
            - POST;
            - PUT."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_INGREDIENTS_PK.format(pk=1))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return


@pytest.mark.django_db
class TestRecipesViewSet():
    """Производит тест вью-сета "RecipesViewSet"."""

    def recipes_post(
            self, client: APIClient, data: dict) -> tuple:
        """Совершает POST-запрос к списку рецептов по эндпоинту
        "/api/v1/recipes/" от лица переданного клиента.
        Возвращает HTTP статус код ответа и JSON данные, приведенные
        к формату Python."""
        response = client.post(
            URL_RECIPES, json.dumps(data), content_type='application/json')
        return response.status_code, json.loads(response.content)

    @pytest.mark.parametrize('is_admin, status_del_other', [
        (False, status.HTTP_403_FORBIDDEN),
        (True, status.HTTP_204_NO_CONTENT)])
    def test_recipes_delete_allowed_author(
            self,
            is_admin: bool,
            status_del_other: status,
            create_recipes_ingredients_tags_users) -> None:
        """""Тест DELETE-запроса на рецепт по эндпоинту "/api/v1/recipes/{pk}/"
        от лица автора рецепта и автора-администратора.
        Рассматриваются случаи:
            - удаление своего рецепта (доступно автору и администратору);
            - удаление чужого рецепта (доступно администратору).
        Используется фикстура "create_recipes_ingredients_tags_users"
        для наполнения тестовой БД рецептами с тегами и ингредиентами."""
        ID_AUTHOR: int = 1
        ID_ANOTHER: int = 2
        author_user: User = User.objects.get(id=ID_AUTHOR)
        author_user.is_staff = is_admin
        author_user.save()
        client: APIClient = auth_token_client(user_id=ID_AUTHOR)
        response = client.delete(f'{URL_RECIPES}{ID_AUTHOR}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        response = client.delete(f'{URL_RECIPES}{ID_ANOTHER}/')
        assert response.status_code == status_del_other
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_recipes_get(
            self,
            client_func,
            create_recipes_ingredients_tags_users) -> None:
        """Тест GET-запроса списка рецептов по эндпоинту "/api/v1/recipes/"
        для анонимного и авторизированного клиента.
        Используется фикстура "create_recipes_ingredients_tags_users"
        для наполнения тестовой БД рецептами с тегами и ингредиентами.
        В классе используется пагинация. В рамках теста производится анализ
        содержимого "results" для первого элемента. Тест непосредственно
        пагинации производится в функции "test_view_sets_pagination"."""
        expected_data: dict[str, any] = {
            'id': 3,
            'tags': [
                {'id': 3,
                 'name': 'test_tag_name_3',
                 'color': '#000003',
                 'slug': 'test_tag_slug_3'}],
            'author': {
                'email': 'test_user_email_3@email.com',
                'id': 3,
                'username': 'test_user_username_3',
                'first_name': 'test_user_first_name_3',
                'last_name': 'test_user_last_name_3',
                'is_subscribed': False},
            'ingredients': [{
                'id': 3,
                'name': 'test_ingredient_name_3',
                'measurement_unit': 'батон',
                'amount': 3.0}],
            'is_favorited': False,
            'is_in_shopping_cart': False,
            'name': 'test_recipe_name_3',
            'image': (
               f'http://testserver/media/'
               f'{Recipes.objects.get(id=3).image.name}'),
            'text': 'test_recipe_text_3',
            'cooking_time': 3}
        client: APIClient = client_func()
        response = client.get(URL_RECIPES)
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        results_pagination: dict = data['results']
        assert results_pagination[0] == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_recipes_get_pk(
            self,
            client_func,
            create_recipes_ingredients_tags_users) -> None:
        """Тест GET-запроса на рецепт по эндпоинту "/api/v1/recipes/{pk}/"
        для анонимного и авторизированного клиента.
        Используется фикстура "create_recipes_ingredients_tags_users"
        для наполнения тестовой БД рецептами с тегами и ингредиентами.
        """
        expected_data: dict[str, any] = {
            'id': 1,
            'tags': [
                {'id': 1,
                 'name': 'test_tag_name_1',
                 'color': '#000001',
                 'slug': 'test_tag_slug_1'}],
            'author': {
                'email': 'test_user_email_1@email.com',
                'id': 1,
                'username': 'test_user_username_1',
                'first_name': 'test_user_first_name_1',
                'last_name': 'test_user_last_name_1',
                'is_subscribed': False},
            'ingredients': [{
                'id': 1,
                'name': 'test_ingredient_name_1',
                'measurement_unit': 'батон',
                'amount': 1.0}],
            'is_favorited': False,
            'is_in_shopping_cart': False,
            'name': 'test_recipe_name_1',
            'image': (
               f'http://testserver/media/'
               f'{Recipes.objects.get(id=1).image.name}'),
            'text': 'test_recipe_text_1',
            'cooking_time': 1}
        client: APIClient = client_func()
        response = client.get(f'{URL_RECIPES}1/')
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == expected_data
        return

    def test_recipes_not_allowed(self, create_recipes_users) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/recipes/":
            - PUT.
        Используется фикстура "create_recipes_users" для наполнения тестовой БД
        рецептами с тегами и ингредиентами."""
        client: APIClient = auth_token_client()
        response = client.put(f'{URL_RECIPES}1/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    # ToDo: раскомментировать, когда будет готов сериализатор
    # @pytest.mark.parametrize('user, response_code', [
    #     ('author', status.HTTP_200_OK),
    #     ('admin', status.HTTP_403_FORBIDDEN)])
    # def test_recipes_patch_allowed_method(
    #         self,
    #         user: str,
    #         response_code: status,
    #         create_recipes_ingredients_tags_users) -> None:
    #     """""Тест PATCH-запроса на рецепт по эндпоинту
    #     "/api/v1/recipes/{pk}/"
    #     для анонимного и авторизированного клиента.
    #     Используется фикстура "create_recipes_ingredients_tags_users"
    #     для наполнения тестовой БД рецептами с тегами и ингредиентами."""
    #     ID_TO_PATCH: int = 1
    #     author_user: User = User.objects.get(id=ID_TO_PATCH)
    #     admin_user: User = User.objects.get(id=(ID_TO_PATCH+1))
    #     admin_user.is_staff = True
    #     admin_user.save()
    #     users: dict[str, User] = {
    #         'author': author_user,
    #         'admin': admin_user}
    #     client: APIClient = auth_token_client(user=users[user])
    #     response = client.patch(f'{URL_RECIPES}{ID_TO_PATCH}/')
    #     assert response.status_code == response_code
    #     return

    VALID_POST_DATA: dict = {
        'ingredients': [
            {
                'id': 1,
                'amount': 1},
            {
                'id': 2,
                'amount': 2}],
        'tags': [
            {
                'id': 1}],
        'image': 'None',
        'name': 'api_create_recipe',
        'text': 'created with post method',
        'cooking_time': 100}
    VALID_POST_DATA_EXP: dict = {
        'id': 1,
        'tags': [
            {'id': 1,
             'name': 'test_tag_name_1',
             'color': '#000001',
             'slug': 'test_tag_slug_1'}],
        'author': {
            'email': 'test_user_email_1@email.com',
            'id': 1,
            'username': 'test_user_username_1',
            'first_name': 'test_user_first_name_1',
            'last_name': 'test_user_last_name_1',
            'is_subscribed': False},
        'ingredients': [
            {'id': 1,
             'name': 'test_ingredient_name_1',
             'measurement_unit': 'батон',
             'amount': 1.0},
            {'id': 2,
             'name': 'test_ingredient_name_2',
             'measurement_unit': 'батон',
             'amount': 2.0}],
        'is_favorited': False,
        'is_in_shopping_cart': False,
        'name': 'api_create_recipe',
        'image': None,
        'text': 'created with post method',
        'cooking_time': 100.5}

    # ToDo: fix test
    # @pytest.mark.parametrize('data, expected_data', [
    #     (VALID_POST_DATA, VALID_POST_DATA_EXP)])
    # def test_recipes_post_allow_create(
    #         self,
    #         data: dict,
    #         expected_data: dict,
    #         create_users) -> None:
    #     """Тест POST-запроса на создание нового пользователя по эндпоинту
    #     "/api/v1/users/" для анонимного и авторизированного клиента.
    #     Передаваемые данные являются заведомо валидными.
    #     Используются фикстуры для наполнения тестовой БД:
    #         - create_tags: теги;
    #         - create_ingredients: ингредиенты."""
    #     test_user: User = User.objects.get(id=1)
    #     client: APIClient = auth_token_client(user=test_user)
    #     assert Recipes.objects.all().count() == 0
    #     response = client.post(
    #         URL_RECIPES, json.dumps(data), content_type='application/json')
    #     #assert response.status_code == status.HTTP_201_CREATED
    #     #data = json.loads(response.content)
    #     assert response.content == 1
    #     return

    def test_shopping_cart_csv(self, create_recipes_ingredients_tags_users):
        """Тест GET-запроса на загрузку списка ингридиентов из пользовательской
        корзины по эндпоинту "/api/v1/recipes/download_shopping_cart/"
        в формате csv."""
        assert Recipes.objects.all().count() == 3
        test_user = User.objects.get(id=1)
        for i in range(1, TEST_FIXTURES_OBJ_AMOUNT+1):
            create_shopping_cart_obj(
                recipe=Recipes.objects.get(id=i),
                user=test_user)
        client: APIClient = auth_token_client()
        response = client.get(path=f'{URL_RECIPES}download_shopping_cart/')
        assert response.status_code == status.HTTP_200_OK
        """Запрещается смешивание байтовых и не байтовых литералов в одной
        строке. В связи с этим, все строки необходимо привести к байтовым
        литералам. Они не поддерживают русский язык, необходимо представить
        "батон" как "\xd0\xb1\xd0\xb0\xd1\x82\xd0\xbe\xd0\xbd"."""
        assert response.content == (
            b'name,measurement_unit,amount\r\n'
            b'test_ingredient_name_3,'
            b'\xd0\xb1\xd0\xb0\xd1\x82\xd0\xbe\xd0\xbd,3.0\r\n'
            b'test_ingredient_name_2,'
            b'\xd0\xb1\xd0\xb0\xd1\x82\xd0\xbe\xd0\xbd,2.0\r\n'
            b'test_ingredient_name_1,'
            b'\xd0\xb1\xd0\xb0\xd1\x82\xd0\xbe\xd0\xbd,1.0\r\n')
        assert response.headers['Content-Type'] == 'text/csv'
        return


@pytest.mark.django_db
class TestTagsViewSet():
    """Производит тест вью-сета "TagsViewSet"."""

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_tags_get(self, client_func, create_tags) -> None:
        """Тест GET-запроса списка тегов по эндпоинту "/api/v1/tags/"
        для анонимного и авторизированного клиента.
        Используется фикстура "create_tags" для наполнения тестовой
        БД тегами.
        В классе используется пагинация. В рамках теста производится анализ
        содержимого "results" для первого элемента. Тест непосредственно
        пагинации производится в функции "test_view_sets_pagination"."""
        expected_data: dict[str, any] = {
            'id': 1,
            'name': 'test_tag_name_1',
            'color': '#000001',
            'slug': 'test_tag_slug_1'}
        client = client_func()
        response = client.get(URL_TAGS)
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        results_pagination: dict = data['results']
        assert results_pagination[0] == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_tags_get_pk(self, client_func, create_tags) -> None:
        """Тест GET-запроса на тег по эндпоинту "/api/v1/users/{pk}/"
        для анонимного и авторизированного клиента.
        Используется фикстура "create_tags" для наполнения тестовой
        БД тегами."""
        client = client_func()
        response = client.get(f'{URL_TAGS}1/')
        assert response.status_code == status.HTTP_200_OK
        data: dict = json.loads(response.content)
        assert data == {
            'id': 1,
            'name': 'test_tag_name_1',
            'color': '#000001',
            'slug': 'test_tag_slug_1'}
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'post', 'put'])
    def test_tags_not_allowed(self, client_func, method: str) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/tags/":
            - DELETE;
            - PATCH;
            - POST;
            - PUT."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_TAGS)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return


@pytest.mark.django_db
@pytest.mark.parametrize('url', [
    URL_INGREDIENTS, URL_RECIPES, URL_TAGS, URL_USERS])
def test_view_sets_pagination(
        url, create_recipes_ingredients_tags_users) -> None:
    """Производит тест пагинации вьюсетов:
        - CustomUserViewSet;
        - RecipesViewSet;
        - TagsViewSet.
    Используется фикстура "create_recipes_ingredients_tags_users"
    для наполнения тестовой БД ингредиентами, пользователями,
    тегами и рецептами."""
    client: APIClient = auth_client()
    response = client.get(url)
    data: dict = json.loads(response.content)
    assert list(data) == ['count', 'next', 'previous', 'results']


# ToDo: разобраться, почему именно тут не работает фикстура
# "test_override_media_root" (картинки сохраняются в исходную папку, указанную
# в модели) из test_models.py и приходится удалять файлы точечно
# в продакшн-каталоге.
def test_delete_temp_media_images() -> None:
    """Проверяет, что тестовые медиа-файлы успешны удалены."""
    folder_path: Path = settings.MEDIA_ROOT / RECIPES_MEDIA_ROOT
    for filename in os.listdir(folder_path):
        if filename.startswith('test_image_') and filename.endswith('.gif'):
            file_path = os.path.join(folder_path, filename)
            os.remove(file_path)
    test_media_files = [
        filename for filename in os.listdir(folder_path)
        if filename.startswith('test') and filename.endswith('.gif')]
    assert len(test_media_files) == 0
