from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone


class Category(models.Model):
    """Модель категории товаров"""
    name = models.CharField(max_length=255, verbose_name=_('Название'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Родительская категория')
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name=_('Изображение')
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_('URL-адрес')
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Порядок отображения')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['display_order', 'name']
        db_table = 'categories'

    def __str__(self):
        return self.name

    @property
    def products_count(self):
        """Количество товаров в категории"""
        return self.products.filter(is_available=True).count()


class Product(models.Model):
    """Модель товара"""
    name = models.CharField(max_length=255, verbose_name=_('Название'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    short_description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_('Краткое описание')
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Категория')
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',  # ← ПРАВИЛЬНО: 'app_label.ModelName'
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Поставщик')
    )

    # Цена и наличие
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Цена')
    )
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Старая цена')
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Количество на складе')
    )
    min_quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Минимальное количество для заказа')
    )

    # Статусы и флаги
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Доступен для заказа')
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Рекомендуемый товар')
    )

    # Изображения
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name=_('Изображение')
    )

    # SEO и идентификация
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_('Артикул')
    )

    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        ordering = ['-created_at']
        db_table = 'products'

    def __str__(self):
        return f"{self.name} - {self.supplier.name}"

    @property
    def available_quantity(self):
        """Доступное для заказа количество"""
        return self.quantity

    @property
    def has_discount(self):
        """Есть ли скидка на товар"""
        return self.old_price and self.old_price > self.price


class ProductCharacteristic(models.Model):
    """Модель характеристики товара"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='characteristics',
        verbose_name=_('Товар')
    )
    name = models.CharField(max_length=255, verbose_name=_('Название характеристики'))
    value = models.CharField(max_length=255, verbose_name=_('Значение'))

    class Meta:
        verbose_name = _('Характеристика товара')
        verbose_name_plural = _('Характеристики товаров')
        db_table = 'product_characteristics'

    def __str__(self):
        return f"{self.name}: {self.value}"

class ProductImage(models.Model):
    """Модель для дополнительных изображений товара"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Товар')
    )
    image = models.ImageField(
        upload_to='products/images/',
        verbose_name=_('Изображение')
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Альтернативный текст')
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Порядок отображения')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        verbose_name = _('Изображение товара')
        verbose_name_plural = _('Изображения товаров')
        ordering = ['display_order']
        db_table = 'product_images'

    def __str__(self):
        return f"Изображение для {self.product.name}"


class ProductReview(models.Model):
    """Модель отзыва о товаре"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Товар')
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Пользователь')
    )
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_('Рейтинг')
    )
    comment = models.TextField(verbose_name=_('Комментарий'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    is_approved = models.BooleanField(default=False, verbose_name=_('Одобрен'))

    class Meta:
        verbose_name = _('Отзыв о товаре')
        verbose_name_plural = _('Отзывы о товарах')
        db_table = 'product_reviews'
        unique_together = ['product', 'user']

    def __str__(self):
        return f"Отзыв {self.user} на {self.product.name}"
