from django.db import models
from django.utils.translation import gettext_lazy as _


class Cart(models.Model):
    user = models.OneToOneField(
        'users.User',  # ← ПРАВИЛЬНО: 'app_label.ModelName'
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('Пользователь')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))

    class Meta:
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')
        db_table = 'cart'

    def __str__(self):
        return f"Корзина {self.user.username}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Корзина')
    )
    product = models.ForeignKey(
        'products.Product',  # ← ПРАВИЛЬНО: 'app_label.ModelName'
        on_delete=models.CASCADE,
        verbose_name=_('Товар')
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Количество'))
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата добавления'))

    class Meta:
        verbose_name = _('Элемент корзина')
        verbose_name_plural = _('Элементы корзины')
        unique_together = ['cart', 'product']
        db_table = 'cart_item'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.product.price * self.quantity
