from rest_framework import serializers
from apps.products.models import Product, Category, ProductCharacteristic, ProductImage, ProductReview


class ProductCharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCharacteristic
        fields = ['name', 'value', 'unit', 'is_important']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main', 'display_order']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    rating_stars = serializers.CharField(source='rating_stars', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_name', 'rating', 'rating_stars', 'title',
                 'comment', 'advantages', 'disadvantages', 'created_at']
        read_only_fields = ['user', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    characteristics = ProductCharacteristicSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    main_image_url = serializers.CharField(source='main_image_url', read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'short_description', 'category', 'category_name',
            'supplier', 'supplier_name', 'price', 'old_price', 'quantity', 'available_quantity',
            'min_quantity', 'is_available', 'is_featured', 'is_new', 'main_image', 'main_image_url',
            'sku', 'slug', 'characteristics', 'images', 'reviews', 'has_discount',
            'discount_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'image', 'slug',
            'display_order', 'is_active', 'products_count', 'children'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        """Рекурсивно получаем дочерние категории"""
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка товаров"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image_url = serializers.CharField(source='main_image_url', read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'short_description', 'category_name', 'supplier_name',
            'price', 'old_price', 'is_available', 'main_image_url',
            'has_discount', 'discount_percentage', 'is_featured', 'is_new'
        ]
