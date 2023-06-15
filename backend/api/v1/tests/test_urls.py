import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def create_users() -> None:
    """Фикстура для наполнения БД заданным числом пользователей."""
    User.objects.create(
        email='test_user@email.com',
        username='test_user',
        first_name='test_user_first_name',
        last_name='test_user_last_name',
        password='test_password')
    return


@pytest.mark.django_db
class TestEndpointAvailability():
    """Производит тест доступности эндпоинтов urlpatterns."""

    def client(self) -> APIClient:
        """Возвращает объект анонимного клиента."""
        return APIClient()

    @pytest.mark.parametrize('url', ['login/', 'logout/'])
    def test_auth_token_endpoints(self, url):
        """Тест доступности эндпоинтов:
            - api/v1/auth/token/login/;
            - api/v1/auth/token/logout/."""
        response = self.client().get(f'/api/v1/auth/token/{url}')
        assert response.status_code not in (
            status.HTTP_301_MOVED_PERMANENTLY,
            status.HTTP_404_NOT_FOUND)

    @pytest.mark.parametrize('url', ['', 'me/', '1/', 'set_password/'])
    def test_users_endpoint(self, url, create_users):
        """Тест доступности эндпоинтов:
            - api/v1/users/;
            - api/v1/users/me/;
            - api/v1/users/{pk}/;
            - api/v1/users/set_password/."""
        response = self.client().get(f'/api/v1/users/{url}')
        assert response.status_code not in (
            status.HTTP_301_MOVED_PERMANENTLY,
            status.HTTP_404_NOT_FOUND)
