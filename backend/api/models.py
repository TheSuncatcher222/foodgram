from django.contrib.auth.models import User
from django.db.models import CASCADE, DateTimeField, ForeignKey, Model


class Subscriptions(Model):
    """Модель подписок."""
    subscriber = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='subscriber',
        verbose_name='подписчик')
    subscription_to = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='subscription_author',
        verbose_name='автор на которого подписка')
    timestamp = DateTimeField(
        auto_now_add=True,
        verbose_name='дата подписки')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (
            f'Подписка {self.subscriber.username} '
            f'на {self.subscriber.username}')
