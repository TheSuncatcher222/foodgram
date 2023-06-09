from django.contrib.auth.models import User
from djoser.serializers import UserSerializer
from rest_framework.serializers import SerializerMethodField

from footgram_app.models import Subscriptions


class CustomUserSerializer(UserSerializer):
    """Переопределяет UserSerializer библиотеки Djoser.
    Добавляет поле 'is_subscribed' в конец списка полей."""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed')

    def get_is_subscribed(self, obj):
        """Показывает статус подписки пользователя в поле 'is_subscribed'.
        Возвращает True, если пользователь имеет подписку, False - если не
        имеет или пользователь не авторизован."""
        if self.context['request'].user.is_anonymous:
            return False
        else:
            return Subscriptions.objects.filter(
                subscriber=self.context['request'].user,
                subscription_to=obj).exists()
