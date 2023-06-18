from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.v1.serializers import CustomUserSerializer, TagsSerializer
from footgram_app.models import Tags

class CustomUserViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) `.../users/ - предоставляет информацию о пользователях при GET запросе,
        создает нового пользователя при POST запросе;
    2) `.../users/pk/ - предоставляет информацию о пользователе с ID=pk
        при GET запросе.
    Дополнительные action-эндпоинты:
    3) `.../users/me/ - предоставляет информацию о текущем пользователе
        (только для авторизированных пользователей!).
    """
    http_method_names = ('get', 'list', 'post')
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        """Обновляет метод передачи объектов модели в сериализатор:
            - устанавливает сортировку объектов по полю "id"
              (используется встроенная модель "User", в которой явным образом
              не задан мета-параметр "ordering")."""
        queryset = super().get_queryset()
        queryset = queryset.order_by('id')
        return queryset

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


class TagsViewSet(ModelViewSet):
    """
    Вью-сет обрабатывает следующие эндпоинты:
    1) `.../tags/ - предоставляет информацию о тегах при GET запросе;
    2) `.../tags/{pk} - предоставляет информацию о теге с ID=pk
       при GET запросе.
    """
    http_method_names = ('get', 'list')
    serializer_class = TagsSerializer
    queryset = Tags.objects.all()
