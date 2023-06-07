from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.v1.serializers import CustomUserSerializer


class CustomUserViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) `.../users/ - предоставляет информацию о пользователях при GET запросе,
        создает нового пользователя при POST запросе.
    2) `.../users/pk/ - предоставляет информацию о пользователе с ID=pk
        при GET запросе.
    Дополнительные action-эндпоинты:
    3) `.../users/me/ - предоставляет информацию о текущем пользователе
        (только для авторизированных пользователей!).
    """
    http_method_names = ('get', 'list', 'post')
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(IsAuthenticated,),
        serializer_class=CustomUserSerializer)
    def me(self, request):
        """Добавляет action-эндпоинт `.../users/me/`."""
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
