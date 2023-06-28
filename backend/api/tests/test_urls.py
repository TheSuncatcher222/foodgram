import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from foodgram_app.tests.test_models import (
    create_ingredient_obj, create_recipe_obj, create_tag_obj, create_user_obj)

URL_UNAVALIABLE_STATUSES: list = [
    status.HTTP_301_MOVED_PERMANENTLY,
    status.HTTP_302_FOUND,
    status.HTTP_303_SEE_OTHER,
    status.HTTP_307_TEMPORARY_REDIRECT,
    status.HTTP_308_PERMANENT_REDIRECT,
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_404_NOT_FOUND,
    status.HTTP_408_REQUEST_TIMEOUT,
    status.HTTP_409_CONFLICT,
    status.HTTP_410_GONE]


@pytest.mark.django_db
class TestEndpointAvailability():
    """Производит тест доступности эндпоинтов в urlpatterns.
    Используется анонимный клиент, так как тестируется именно доступность
    эндпоинтов, а не права доступа к ним."""

    def client(self) -> APIClient:
        """Возвращает объект анонимного клиента."""
        return APIClient()

    @pytest.mark.parametrize('url', ['', '1/'])
    def test_ingredients(self, url):
        """
        Тест доступности эндпоинтов:
            - /api/v1/ingredients/
            - /api/v1/ingredients/1/
        """
        create_ingredient_obj(num=1)
        response = self.client().get(f'/api/v1/ingredients/{url}')
        assert response.status_code not in URL_UNAVALIABLE_STATUSES
        return

    @pytest.mark.parametrize('url', ['login/', 'logout/'])
    def test_auth_token_endpoints(self, url):
        """
        Тест доступности эндпоинтов:
            - /api/v1/auth/token/login/
            - /api/v1/auth/token/logout/
        """
        response = self.client().get(f'/api/v1/auth/token/{url}')
        assert response.status_code not in URL_UNAVALIABLE_STATUSES
        return

    @pytest.mark.parametrize('url', [
        '',
        '1/',
        '1/favorite/',
        '1/shopping_cart/',
        'download_shopping_cart/'])
    def test_recipes_endpoint(self, url):
        """
        Тест доступности эндпоинтов:
            - /api/v1/recipes/
            - /api/v1/recipes/download_shopping_cart/
            - /api/v1/recipes/{pk}/
            - /api/v1/recipes/{pk}/favorite/
            - /api/v1/recipes/{pk}/shopping_cart/
        """
        test_user: User = create_user_obj(num=1)
        create_recipe_obj(num=1, user=test_user)
        response = self.client().get(f'/api/v1/recipes/{url}')
        assert response.status_code not in URL_UNAVALIABLE_STATUSES
        return

    @pytest.mark.parametrize('url', ['', '1/'])
    def test_tags_endpoint(self, url):
        """
        Тест доступности эндпоинтов:
            - /api/v1/tags/
            - /api/v1/tags/{pk}/
        """
        create_tag_obj(num=1, unique_color='#000')
        response = self.client().get(f'/api/v1/tags/{url}')
        assert response.status_code not in URL_UNAVALIABLE_STATUSES
        return

    @pytest.mark.parametrize('url', [
        '', 'me/', '1/', '1/subscribe/', 'set_password/', 'subscriptions/'])
    def test_users_endpoint(self, url):
        """
        Тест доступности эндпоинтов:
            - /api/v1/users/
            - /api/v1/users/me/
            - /api/v1/users/{pk}/
            - /api/v1/users/{pk}/subscribe/
            - /api/v1/users/set_password/
            - /api/v1/users/subscriptions/
        """
        create_user_obj(num=1)
        response = self.client().get(f'/api/v1/users/{url}')
        assert response.status_code not in URL_UNAVALIABLE_STATUSES
        return


@pytest.mark.django_db
class TestThrottling():
    """Производит тест троттлинга эндпоинтов urlpatterns."""

    # ToDo: понять, почему сохраняется количество посещений на сайте между
    # различными тестами.
    @pytest.mark.skip(reason=(
            'Results are succeed, but further test will be failed with 429'))
    def test_throttling(self) -> None:
        """Производит тест троттлинга при совершении большого количества
        обращений к серверу по методу GET.
        В качестве эндпоинта выбран /api/v1/ingredients/."""
        THROTTLING_LIMIT: int = 1000
        create_ingredient_obj(num=1)
        client: APIClient = APIClient()
        for _ in range(THROTTLING_LIMIT-1):
            client.get('/api/v1/ingredients/')
        response = client.get('/api/v1/ingredients/')
        assert response.status_code == status.HTTP_200_OK
        response = client.get('/api/v1/ingredients/')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
