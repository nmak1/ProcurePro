from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .models import Supplier, SupplierContact
from .serializers import (
    SupplierSerializer, SupplierCreateSerializer, SupplierUpdateSerializer,
    SupplierContactSerializer, SupplierContactCreateSerializer,
    SupplierStatsSerializer, SupplierOrderSerializer
)


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet для управления поставщиками"""
    permission_classes = [IsAdminUser]  # Только администраторы могут управлять поставщиками
    queryset = Supplier.objects.select_related('user').prefetch_related('contacts', 'products')

    def get_serializer_class(self):
        if self.action == 'create':
            return SupplierCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SupplierUpdateSerializer
        return SupplierSerializer

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Получение статистики поставщика"""
        supplier = self.get_object()

        # Статистика продуктов
        total_products = supplier.products.count()
        available_products = supplier.products.filter(is_available=True).count()

        # Статистика заказов
        from backend.apps.orders.models import OrderItem
        order_items = OrderItem.objects.filter(supplier=supplier)
        total_orders = order_items.values('order').distinct().count()
        pending_orders = order_items.filter(order__status='pending').values('order').distinct().count()
        completed_orders = order_items.filter(order__status='delivered').values('order').distinct().count()
        total_revenue = sum(item.total_price for item in order_items.filter(order__status='delivered'))

        stats_data = {
            'total_products': total_products,
            'available_products': available_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue
        }

        serializer = SupplierStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Получение заказов поставщика"""
        supplier = self.get_object()

        from backend.apps.orders.models import OrderItem
        order_items = OrderItem.objects.filter(
            supplier=supplier
        ).select_related('order', 'order__user', 'product')

        orders_data = {}
        for item in order_items:
            order = item.order
            if order.id not in orders_data:
                orders_data[order.id] = {
                    'order_number': order.order_number,
                    'customer_email': order.user.email,
                    'status': order.status,
                    'total_amount': order.total_amount,
                    'created_at': order.created_at,
                    'items': []
                }

            orders_data[order.id]['items'].append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price)
            })

        serializer = SupplierOrderSerializer(list(orders_data.values()), many=True)
        return Response(serializer.data)


class SupplierContactViewSet(viewsets.ModelViewSet):
    """ViewSet для управления контактами поставщиков"""
    permission_classes = [IsAdminUser]
    serializer_class = SupplierContactSerializer

    def get_queryset(self):
        return SupplierContact.objects.filter(supplier_id=self.kwargs['supplier_pk'])

    def get_serializer_class(self):
        if self.action == 'create':
            return SupplierContactCreateSerializer
        return SupplierContactSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['supplier_id'] = self.kwargs['supplier_pk']
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supplier_products(request):
    """Получение товаров поставщика (для самого поставщика)"""
    try:
        supplier = request.user.supplier_profile
        products = supplier.products.all()
        from backend.apps.products.serializers import ProductSerializer
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    except Supplier.DoesNotExist:
        return Response(
            {'error': 'User is not a supplier'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_orders(request):
    """Включение/выключение приема заказов"""
    try:
        supplier = request.user.supplier_profile
        supplier.accepts_orders = not supplier.accepts_orders
        supplier.save()
        return Response({
            'accepts_orders': supplier.accepts_orders,
            'message': f'Order acceptance {"enabled" if supplier.accepts_orders else "disabled"}'
        })
    except Supplier.DoesNotExist:
        return Response(
            {'error': 'User is not a supplier'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supplier_orders(request):
    """Получение заказов поставщика (для самого поставщика)"""
    try:
        supplier = request.user.supplier_profile

        # Получаем заказы, содержащие товары этого поставщика
        from backend.apps.orders.models import OrderItem
        order_items = OrderItem.objects.filter(
            supplier=supplier
        ).select_related('order', 'order__user', 'product')

        orders_data = {}
        for item in order_items:
            order = item.order
            if order.id not in orders_data:
                orders_data[order.id] = {
                    'order_number': order.order_number,
                    'customer_email': order.user.email,
                    'status': order.status,
                    'total_amount': order.total_amount,
                    'created_at': order.created_at,
                    'items': []
                }

            orders_data[order.id]['items'].append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price)
            })

        return Response(list(orders_data.values()))

    except Supplier.DoesNotExist:
        return Response(
            {'error': 'User is not a supplier'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supplier_stats(request):
    """Получение статистики поставщика (для самого поставщика)"""
    try:
        supplier = request.user.supplier_profile

        # Статистика продуктов
        total_products = supplier.products.count()
        available_products = supplier.products.filter(is_available=True).count()

        # Статистика заказов
        from backend.apps.orders.models import OrderItem
        order_items = OrderItem.objects.filter(supplier=supplier)
        total_orders = order_items.values('order').distinct().count()
        pending_orders = order_items.filter(order__status='pending').values('order').distinct().count()
        completed_orders = order_items.filter(order__status='delivered').values('order').distinct().count()
        total_revenue = sum(item.total_price for item in order_items.filter(order__status='delivered'))

        stats_data = {
            'total_products': total_products,
            'available_products': available_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue
        }

        serializer = SupplierStatsSerializer(stats_data)
        return Response(serializer.data)

    except Supplier.DoesNotExist:
        return Response(
            {'error': 'User is not a supplier'},
            status=status.HTTP_400_BAD_REQUEST
        )