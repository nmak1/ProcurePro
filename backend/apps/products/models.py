from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительская категория'
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def products_count(self):
        return self.products.filter(is_available=True).count()


class ProductCharacteristic(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название характеристики')
    value = models.CharField(max_length=255, verbose_name='Значение')
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='characteristics',
        verbose_name='Товар'
    )

    class Meta:
        verbose_name = 'Характеристика товара'
        verbose_name_plural = 'Характеристики товаров'

    def __str__(self):
        return f"{self.name}: {self.value}"


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория'
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Поставщик'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество на складе')
    min_quantity = models.PositiveIntegerField(default=1, verbose_name='Минимальное количество для заказа')
    is_available = models.BooleanField(default=True, verbose_name='Доступен для заказа')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        # Автоматически обновляем доступность товара
        if self.quantity < self.min_quantity:
            self.is_available = False
        super().save(*args, **kwargs)