from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('client', 'Клиент'),
        ('supplier', 'Поставщик'),
        ('admin', 'Администратор'),
    )

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='client',
        verbose_name=_('Тип пользователя')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Телефон')
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Название компании')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('Адрес')
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
