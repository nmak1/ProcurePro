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
        default='client'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    company_name = models.CharField(max_length=255, blank=True, verbose_name='Название компании')
    address = models.TextField(blank=True, verbose_name='Адрес')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_supplier(self):
        return self.user_type == 'supplier'

    @property
    def is_client(self):
        return self.user_type == 'client'