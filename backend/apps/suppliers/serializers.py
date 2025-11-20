from rest_framework import serializers
from .models import Supplier, SupplierContact


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = ['id', 'name', 'position', 'email', 'phone']


class SupplierSerializer(serializers.ModelSerializer):
    contacts = SupplierContactSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'name', 'type', 'email', 'phone', 'address',
            'is_active', 'accepts_orders', 'contacts', 'products_count',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def get_products_count(self, obj):
        return obj.products.count()


class SupplierCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания поставщика"""
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Supplier
        fields = [
            'name', 'type', 'email', 'phone', 'address',
            'first_name', 'last_name', 'password'
        ]

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Извлекаем данные для пользователя
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password')

        # Создаем пользователя
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_supplier=True
        )

        # Создаем поставщика
        supplier = Supplier.objects.create(user=user, **validated_data)
        return supplier


class SupplierUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления поставщика"""

    class Meta:
        model = Supplier
        fields = [
            'name', 'type', 'email', 'phone', 'address',
            'is_active', 'accepts_orders'
        ]


class SupplierContactCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания контакта поставщика"""

    class Meta:
        model = SupplierContact
        fields = ['name', 'position', 'email', 'phone']

    def create(self, validated_data):
        # Получаем supplier_id из контекста
        supplier_id = self.context.get('supplier_id')
        if supplier_id:
            return SupplierContact.objects.create(
                supplier_id=supplier_id,
                **validated_data
            )
        raise serializers.ValidationError("Supplier ID is required")


class SupplierStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики поставщика"""
    total_products = serializers.IntegerField()
    available_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class SupplierOrderSerializer(serializers.Serializer):
    """Сериализатор для заказов поставщика"""
    order_number = serializers.CharField()
    customer_email = serializers.CharField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()
    items = serializers.ListField(child=serializers.DictField())