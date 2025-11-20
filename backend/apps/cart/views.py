from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer


class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self.get_object()
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        try:
            from backend.apps.products.models import Product
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found or not available'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем максимальное количество
        if quantity > product.max_order_quantity:
            return Response(
                {'error': f'Maximum order quantity is {product.max_order_quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.max_order_quantity:
                return Response(
                    {'error': f'Total quantity would exceed maximum of {product.max_order_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request, item_id=None):
        cart = self.get_object()

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart = self.get_object()
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'})

    @action(detail=False, methods=['post'])
    def update_quantity(self, request, item_id=None):
        cart = self.get_object()

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            serializer = UpdateCartItemSerializer(cart_item, data=request.data)
            serializer.is_valid(raise_exception=True)

            quantity = serializer.validated_data['quantity']

            # Проверяем максимальное количество
            if quantity > cart_item.product.max_order_quantity:
                return Response(
                    {'error': f'Maximum order quantity is {cart_item.product.max_order_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверяем минимальное количество
            if quantity < cart_item.product.min_order_quantity:
                return Response(
                    {'error': f'Minimum order quantity is {cart_item.product.min_order_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save()
            return Response(CartSerializer(cart).data)

        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )