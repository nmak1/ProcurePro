from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order, OrderItem, DeliveryAddress
from .serializers import OrderSerializer, OrderCreateSerializer, DeliveryAddressSerializer
from apps.cart.models import Cart, CartItem
from apps.core.tasks import send_order_confirmation_email, send_order_to_admin


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

        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product', 'product__supplier').all()

        if not cart_items:
            return Response(
                {'error': 'Cart is empty'},
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

            if not product.is_available:
                continue

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


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryAddressSerializer

    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)