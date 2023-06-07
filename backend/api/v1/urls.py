from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView, UserViewSet
from rest_framework.routers import DefaultRouter

from api.v1.views import CustomUserViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/token/login/',
         TokenCreateView.as_view(),
         name='token_create'),
    path('auth/token/logout/',
         TokenDestroyView.as_view(),
         name='token_destroy'),
    path('users/set_password/',
         UserViewSet.as_view({'post': 'set_password'}),
         name='set_password'),
    path('', include(router.urls)),
]
