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
    create_recipe_tag_obj, create_tag_obj, create_user_obj,
    create_user_obj_with_hash)

URL_API_V1: str = '/api/v1/'
URL_AUTH: str = f'{URL_API_V1}auth/token/'
URL_AUTH_LOGIN: str = f'{URL_AUTH}login/'
URL_AUTH_LOGOUT: str = f'{URL_AUTH}logout/'
URL_RECIPES: str = f'{URL_API_V1}recipes/'
URL_TAGS: str = f'{URL_API_V1}tags/'
URL_USERS: str = f'{URL_API_V1}users/'
URL_USERS_ME: str = f'{URL_USERS}me/'
URL_USERS_SET_PASSWORD: str = f'{URL_USERS}set_password/'

TEST_FIXTURES_OBJ_COUNT: int = 3


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
def create_recipes_users() -> None:
    """Фикстура для наполнения БД заданным числом рецептов.
    Также создает пользователей, которые являются авторами этих рецептов."""
    for i in range(1, TEST_FIXTURES_OBJ_COUNT+1):
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
    for i in range(1, TEST_FIXTURES_OBJ_COUNT+1):
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
    for i in range(1, TEST_FIXTURES_OBJ_COUNT+1):
        create_tag_obj(num=i)
    return


@pytest.fixture()
def create_users() -> None:
    """Фикстура для наполнения БД заданным числом пользователей."""
    for i in range(1, TEST_FIXTURES_OBJ_COUNT+1):
        create_user_obj(num=i)
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
    def test_users_get(self, client_func: APIClient, create_users) -> None:
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
        data: dict = self.users_get(client=client_func())
        results_pagination: dict = data['results']
        assert len(results_pagination) == TEST_FIXTURES_OBJ_COUNT
        assert results_pagination[0] == expected_data
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    @pytest.mark.parametrize('method', ['delete', 'patch', 'put'])
    def test_users_not_allowed_methods(
            self, client_func: APIClient, method) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/users/":
            - DELETE;
            - PATCH;
            - PUT."""
        client: APIClient = client_func()
        response = getattr(client, method)(URL_TAGS)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_post_allow_create(self, client_func: APIClient) -> None:
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
            self,
            client_func: APIClient,
            data: dict,
            expected_data: dict,
            create_users) -> None:
        """Тест POST-запроса на создание нового пользователя по эндпоинту
        "/api/v1/users/" для анонимного и авторизированного клиента.
        Передаваемые данные являются заведомо не валидными валидными."""
        self.users_post(
            client=client_func(),
            data=data,
            expected_data=expected_data,
            expected_status=status.HTTP_400_BAD_REQUEST,
            expected_users_count=TEST_FIXTURES_OBJ_COUNT)
        return

    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_users_pk(self, client_func: APIClient, create_users) -> None:
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
        client: APIClient = auth_client()
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

    def test_users_set_password(self) -> None:
        """Тест POST-запроса на страницу изменения пароля по эндпоинту
        "/api/users/set_password/" для авторизованного клиента."""
        test_user: User = create_user_obj_with_hash(num=1)
        token, _ = Token.objects.get_or_create(user=test_user)
        client: APIClient = anon_client()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        NEW_PASSWORD: str = 'some_new_data_pass'
        data: dict = {
            'current_password': 'test_user_password_1',
            'new_password': NEW_PASSWORD}
        response = client.post(
            URL_USERS_SET_PASSWORD,
            json.dumps(data),
            content_type='application/json')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_users_get_token(self) -> None:
        """Тест POST-запроса на страницу получения токена по эндпоинту
        "/api/auth/token/login/" для анонимного клиента."""
        test_user: User = create_user_obj_with_hash(num=1)
        token, _ = Token.objects.get_or_create(user=test_user)
        client = anon_client()
        data: dict = {
            'username': 'test_user_username_1',
            'password': 'test_user_password_1'}
        response = client.post(
            URL_AUTH_LOGIN,
            json.dumps(data),
            content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        content = json.loads(response.content)
        assert content['auth_token'] == token.key


@pytest.mark.django_db
class TestRecipesViewSet():
    """Производит тест вью-сета "RecipesViewSet"."""

    def recipes_post(
            self, client: APIClient, data: dict) -> tuple[status, dict]:
        """Совершает POST-запрос к списку рецептов по эндпоинту
        "/api/v1/recipes/" от лица переданного клиента.
        Возвращает HTTP статус код ответа и JSON данные, приведенные
        к формату Python."""
        response = client.post(
            URL_RECIPES, json.dumps(data), content_type='application/json')
        status_code: status = response.status_code
        data: dict = json.loads(response.content)
        return status_code, data

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
        token, _ = Token.objects.get_or_create(user=author_user)
        client: APIClient = anon_client()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = client.delete(f'{URL_RECIPES}{ID_AUTHOR}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        response = client.delete(f'{URL_RECIPES}{ID_ANOTHER}/')
        assert response.status_code == status_del_other
        return

    # ToDo: update tests: add ingredients.amount
    @pytest.mark.parametrize('client_func', [anon_client, auth_client])
    def test_recipes_get(
            self,
            client_func: APIClient,
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
                # 'amount': 3
            }],
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
            client_func: APIClient,
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
            #     'amount': 1
            }],
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

    def test_recipes_not_allowed_methods(self, create_recipes_users) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/recipes/":
            - PUT.
        Используется фикстура "create_recipes_users" для наполнения тестовой БД
        рецептами с тегами и ингредиентами."""
        test_user: User = User.objects.get(id=1)
        token, _ = Token.objects.get_or_create(user=test_user)
        client: APIClient = anon_client()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = client.put(f'{URL_RECIPES}1/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        return

    # @pytest.mark.parametrize('user, response_code', [
    #     ('author', status.HTTP_200_OK),
    #     ('admin', status.HTTP_403_FORBIDDEN)])
    # def test_recipes_patch_allowed_method(
    #         self,
    #         user: str,
    #         response_code: status,
    #         create_recipes_ingredients_tags_users) -> None:
    #     """""Тест PATCH-запроса на рецепт по эндпоинту "/api/v1/recipes/{pk}/"
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
    #     token, _ = Token.objects.get_or_create(user=users[user])
    #     client: APIClient = anon_client()
    #     client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
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
             'amount': 1},
            {'id': 2,
             'name': 'test_ingredient_name_2',
             'measurement_unit': 'батон',
             'amount': 2}],
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
    #     client: APIClient = anon_client()
    #     test_user: User = User.objects.get(id=1)
    #     token, _ = Token.objects.get_or_create(user=test_user)
    #     client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    #     assert Recipes.objects.all().count() == 0
    #     response = client.post(
    #         URL_RECIPES, json.dumps(data), content_type='application/json')
    #     #assert response.status_code == status.HTTP_201_CREATED
    #     #data = json.loads(response.content)
    #     assert response.content == 1

    @pytest.mark.parametrize('user, response_code', [
        ('auth_user', status.HTTP_405_METHOD_NOT_ALLOWED),
        ('anon_user', status.HTTP_401_UNAUTHORIZED)])
    def test_tags_put_allowed_method(
            self, user: str, response_code: status, create_users) -> None:
        """Тест запрета на CRUD запросы к эндпоинту "/api/v1/tags/":
            - PUT."""
        auth_user = User.objects.get(id=1)
        token, _ = Token.objects.get_or_create(user=auth_user)
        users_tokens: dict[str, User] = {
            'auth_user': token,
            'anon_user': ''}
        client: APIClient = anon_client()
        client.credentials(HTTP_AUTHORIZATION=f'Token {users_tokens[user]}')
        response = client.put(f'{URL_RECIPES}1/')
        assert response.status_code == response_code
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
    def test_tags_not_allowed_methods(self, client_func, method) -> None:
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
@pytest.mark.parametrize('url', [URL_RECIPES, URL_TAGS, URL_USERS])
def test_view_sets_pagination(
        url, create_recipes_users, create_tags) -> None:
    """Производит тест пагинации вьюсетов:
        - CustomUserViewSet;
        - RecipesViewSet;
        - TagsViewSet.
    Используется фикстуры для наполнения тестовой БД:
        "create_recipes_users" - рецептами и пользователями;
        "create_tags" - тегами."""
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
