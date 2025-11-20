from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order, OrderItem, DeliveryAddress
from .serializers import OrderSerializer, OrderCreateSerializer, DeliveryAddressSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Импорты внутри метода чтобы избежать циклических импортов
        from backend.apps.cart.models import Cart, CartItem
        from backend.apps.core.tasks import send_order_confirmation_email, send_order_to_admin

        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product', 'product__supplier').all()

        if not cart_items:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем доступность товаров
        unavailable_products = []
        for cart_item in cart_items:
            if not cart_item.product.is_available:
                unavailable_products.append(cart_item.product.name)

        if unavailable_products:
            return Response(
                {'error': f'Some products are not available: {", ".join(unavailable_products)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create order
        order = Order.objects.create(
            user=request.user,
            delivery_address=serializer.validated_data['delivery_address'],
            notes=serializer.validated_data.get('notes', '')
        )

        total_amount = 0
        order_items = []

        for cart_item in cart_items:
            product = cart_item.product

            order_item = OrderItem(
                order=order,
                product=product,
                supplier=product.supplier,
                quantity=cart_item.quantity,
                unit_price=product.price
            )
            order_items.append(order_item)
            total_amount += order_item.total_price

        OrderItem.objects.bulk_create(order_items)
        order.total_amount = total_amount
        order.save()

        # Clear cart
        cart.items.all().delete()

        # Send emails asynchronously
        send_order_confirmation_email.delay(order.id)
        send_order_to_admin.delay(order.id)

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена заказа"""
        order = self.get_object()

        if order.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'Order cannot be cancelled in its current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()

        return Response({
            'message': 'Order cancelled successfully',
            'status': order.status
        })


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryAddressSerializer

    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Установка адреса по умолчанию"""
        address = self.get_object()

        # Сбрасываем все адреса по умолчанию
        DeliveryAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)

        # Устанавливаем текущий адрес как default
        address.is_default = True
        address.save()

        return Response({'message': 'Default address updated successfully'})