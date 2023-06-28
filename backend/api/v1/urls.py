from django.urls import include, path
from djoser.views import TokenDestroyView, UserViewSet
from rest_framework.routers import DefaultRouter

from api.v1.views import (
    csv_import_ingredients, custom_user_login,
    CustomUserViewSet, IngredientsViewSet, RecipesViewSet, TagsViewSet)

roots: list[dict] = [
    {'path': r'ingredients',
     'viewset': IngredientsViewSet,
     'basename': 'ingredients'},
    {'path': r'recipes',
     'viewset': RecipesViewSet,
     'basename': 'recipes'},
    {'path': r'tags',
     'viewset': TagsViewSet,
     'basename': 'tags'},
    {'path': r'users',
     'viewset': CustomUserViewSet,
     'basename': 'users'}]
router = DefaultRouter()
for root in roots:
    router.register(root['path'], root['viewset'], basename=root['basename'])

urlpatterns = [
    path('auth/token/login/',
         custom_user_login,
         name='token_create'),
    path('auth/token/logout/',
         TokenDestroyView.as_view(),
         name='token_destroy'),
    path('users/set_password/',
         UserViewSet.as_view({'post': 'set_password'}),
         name='set_password'),
    path('csv-import/ingredients/',
         csv_import_ingredients,
         name='ingredients_csv_import'),
    path('', include(router.urls)),
]
