from django.db import models
from django.utils.translation import gettext_lazy as _


class Supplier(models.Model):
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='supplier_profile',
        verbose_name='Пользователь'
    )
    name = models.CharField(max_length=255, verbose_name='Название компании')
    description = models.TextField(blank=True, verbose_name='Описание')
    accepts_orders = models.BooleanField(default=True, verbose_name='Принимает заказы')
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierContact(models.Model):
    CONTACT_TYPE_CHOICES = (
        ('phone', 'Телефон'),
        ('email', 'Email'),
        ('address', 'Адрес'),
        ('other', 'Другое'),
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='Поставщик'
    )
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES, verbose_name='Тип контакта')
    value = models.CharField(max_length=255, verbose_name='Значение')
    is_primary = models.BooleanField(default=False, verbose_name='Основной контакт')

    class Meta:
        verbose_name = 'Контакт поставщика'
        verbose_name_plural = 'Контакты поставщиков'

    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.value}"