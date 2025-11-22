from django.db import models
from django.utils.translation import gettext_lazy as _


class Supplier(models.Model):
    user = models.OneToOneField(
        'users.User',  # ← ПРАВИЛЬНО: 'app_label.ModelName'
        on_delete=models.CASCADE,
        related_name='supplier_profile',
        verbose_name=_('Пользователь')
    )
    name = models.CharField(max_length=255, verbose_name=_('Название компании'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))

    # Дополнительные поля для поставщика
    type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Тип поставщика')
    )
    address = models.TextField(blank=True, verbose_name=_('Адрес'))

    accepts_orders = models.BooleanField(default=True, verbose_name=_('Принимает заказы'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активный'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата регистрации'))

    class Meta:
        verbose_name = _('Поставщик')
        verbose_name_plural = _('Поставщики')
        ordering = ['name']
        db_table = 'suppliers'

    def __str__(self):
        return self.name


class SupplierContact(models.Model):
    """Контактные лица поставщика"""
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('Поставщик')
    )
    name = models.CharField(max_length=255, verbose_name=_('ФИО'))
    position = models.CharField(max_length=255, blank=True, verbose_name=_('Должность'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Телефон'))

    class Meta:
        verbose_name = _('Контакт поставщика')
        verbose_name_plural = _('Контакты поставщиков')
        db_table = 'supplier_contacts'

    def __str__(self):
        return f"{self.name} - {self.supplier.name}"
