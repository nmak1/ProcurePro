from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    )

    user = models.ForeignKey(
        'users.User',  # ← ПРАВИЛЬНО: 'app_label.ModelName'
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Пользователь')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Общая сумма')
    )
    shipping_address = models.TextField(verbose_name=_('Адрес доставки'))
    notes = models.TextField(blank=True, verbose_name=_('Примечания'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']
        db_table = 'orders'

    def __str__(self):
        return f"Заказ #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Заказ')
    )
    product = models.ForeignKey(
        'products.Product',  # ← ПРАВИЛЬНО: 'app_label.ModelName'
        on_delete=models.CASCADE,
        verbose_name=_('Товар')
    )
    quantity = models.PositiveIntegerField(verbose_name=_('Количество'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Цена за единицу'))

    class Meta:
        verbose_name = _('Элемент заказа')
        verbose_name_plural = _('Элементы заказа')
        db_table = 'order_items'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.price
