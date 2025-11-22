from rest_framework import serializers
from apps.cart.models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    product_image = serializers.SerializerMethodField()
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    supplier_name = serializers.CharField(source='product.supplier.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_available = serializers.BooleanField(source='product.is_available', read_only=True)
    max_quantity = serializers.IntegerField(source='product.quantity', read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_id',
            'product_name',
            'product_price',
            'product_sku',
            'product_image',
            'supplier_name',
            'quantity',
            'total_price',
            'is_available',
            'max_quantity',
            'added_at'
        ]
        read_only_fields = ['added_at']

    def get_product_image(self, obj):
        """Получить URL изображения товара"""
        if obj.product.image:
            return obj.product.image.url
        return None

    def validate_quantity(self, value):
        """Валидация количества"""
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть положительным числом")
        if value > 1000:  # Максимальное ограничение
            raise serializers.ValidationError("Слишком большое количество")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_empty = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'items',
            'total_items',
            'total_amount',
            'is_empty',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000, default=1)

    def validate_product_id(self, value):
        """Проверить существование товара"""
        from apps.products.models import Product
        try:
            product = Product.objects.get(id=value)
            if not product.is_available:
                raise serializers.ValidationError("Товар недоступен для заказа")
        except Product.DoesNotExist:
            raise serializers.ValidationError("Товар не найден")
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0, max_value=1000)

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Для удаления товара используйте метод DELETE")
        return value
