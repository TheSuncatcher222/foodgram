"""
Создает пермишены для API проекта "Foodgram".

Классы-пермишены:
    - IsAuthorOrAdminOrReadOnly.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

from foodgram_app.models import Recipes


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """
    Обновляет права доступа к вью-сету:
        - DELETE: разрешено автору рецепта или администратору;
        - GET: разрешено всем;
        - PATCH: разрешено автору рецепта;
        - POST: разрешено авторизованным пользователям;
        - PUT: разрешено автору рецепта.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Устанавливает права доступа к объектам модели:
            - GET: разрешено всем;
            - POST: разрешено авторизованным пользователям.
        """
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(
            self, request: Request, view: APIView, obj: Recipes) -> bool:
        """
        Устанавливает права доступа к объекту модели:
            - DELETE: разрешено автору рецепта или администратору;
            - PATCH: разрешено автору рецепта;
            - PUT: разрешено автору рецепта.
        """
        if request.method == 'DELETE':
            return self.is_author_or_admin(request, view, obj)
        elif request.method in ('PATCH', 'PUT'):
            return self.is_author(request, view, obj)
        return True

    def is_author_or_admin(
            self, request: Request, view: APIView, obj: Recipes) -> bool:
        """Возвращает True, если пользователь является создателем объекта
        (указан в поле "author") или является администратором ("is_staff")."""
        return obj.author == request.user or request.user.is_staff

    def is_author(self, request: Request, view: APIView, obj: Recipes) -> bool:
        """Возвращает True, если пользователь является создателем объекта
        (указан в поле "author")."""
        return obj.author == request.user
