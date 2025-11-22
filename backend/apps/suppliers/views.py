from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.suppliers.models import Supplier
from apps.suppliers.serializers import SupplierSerializer


class SupplierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Supplier.objects.filter(is_active=True).prefetch_related('contacts', 'products')
    serializer_class = SupplierSerializer


class SupplierManagementViewSet(viewsets.ModelViewSet):
    """API для управления поставщиками (только для поставщиков)"""
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Только поставщики могут управлять своими данными
        if hasattr(self.request.user, 'supplier_profile'):
            return Supplier.objects.filter(user=self.request.user)
        return Supplier.objects.none()

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """Получить товары поставщика"""
        try:
            supplier = request.user.supplier_profile
            from apps.products.models import Product
            from apps.products.serializers import ProductSerializer

            products = Product.objects.filter(supplier=supplier)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)

        except Supplier.DoesNotExist:
            return Response(
                {'error': 'Профиль поставщика не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def toggle_orders(self, request):
        """Включить/выключить прием заказов"""
        try:
            supplier = request.user.supplier_profile
            supplier.accepts_orders = not supplier.accepts_orders
            supplier.save()

            status_text = 'включен' if supplier.accepts_orders else 'выключен'
            return Response({
                'detail': f'Прием заказов {status_text}',
                'accepts_orders': supplier.accepts_orders
            })

        except Supplier.DoesNotExist:
            return Response(
                {'error': 'Профиль поставщика не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Получить заказы с товарами поставщика"""
        try:
            supplier = request.user.supplier_profile

            from apps.orders.models import OrderItem
            from apps.orders.serializers import OrderItemSerializer

            # Получаем элементы заказов с товарами этого поставщика
            order_items = OrderItem.objects.filter(
                product__supplier=supplier
            ).select_related('order', 'product', 'order__user')

            # Группируем по заказам
            orders_data = {}
            for item in order_items:
                order_id = item.order.id
                if order_id not in orders_data:
                    orders_data[order_id] = {
                        'order_id': order_id,
                        'status': item.order.get_status_display(),
                        'created_at': item.order.created_at,
                        'total_amount': item.order.total_amount,
                        'customer_email': item.order.user.email,
                        'items': []
                    }
                orders_data[order_id]['items'].append({
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'total_price': item.total_price
                })

            return Response(list(orders_data.values()))

        except Supplier.DoesNotExist:
            return Response(
                {'error': 'Профиль поставщика не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика поставщика"""
        try:
            supplier = request.user.supplier_profile

            from apps.products.models import Product
            from apps.orders.models import OrderItem

            total_products = supplier.products.count()
            available_products = supplier.products.filter(is_available=True).count()

            # Статистика заказов
            order_items = OrderItem.objects.filter(product__supplier=supplier)
            total_orders = order_items.values('order').distinct().count()

            # Выручка
            total_revenue = sum(item.total_price for item in order_items)

            return Response({
                'total_products': total_products,
                'available_products': available_products,
                'total_orders': total_orders,
                'total_revenue': total_revenue
            })

        except Supplier.DoesNotExist:
            return Response(
                {'error': 'Профиль поставщика не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
