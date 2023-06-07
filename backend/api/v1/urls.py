from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.v1.views import CustomUserViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
