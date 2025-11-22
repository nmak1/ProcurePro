from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.cart.models import Cart, CartItem
from apps.cart.serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer
)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).with_totals()

    def get_object(self):
        """Получить или создать корзину пользователя"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        """Получить корзину пользователя"""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Очистить корзину"""
        cart = self.get_object()
        cart.clear()
        return Response(
            {'detail': 'Корзина очищена'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Краткая информация о корзине"""
        cart = self.get_object()
        return Response({
            'total_items': cart.total_items,
            'total_amount': cart.total_amount,
            'is_empty': cart.is_empty()
        })


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']

            from apps.products.models import Product  # ← ИЗМЕНИТЕ ИМПОРТ
            product = get_object_or_404(Product, id=product_id, is_available=True)

            # Проверка доступного количества
            if product.quantity < quantity:
                return Response(
                    {
                        'error': 'Недостаточно товара на складе',
                        'available_quantity': product.quantity
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item = cart.add_product(product, quantity)

            return Response(
                CartItemSerializer(cart_item).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']

            cart_item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user
            )

            # Проверка доступного количества
            if cart_item.product.quantity < quantity:
                return Response(
                    {
                        'error': 'Недостаточно товара на складе',
                        'available_quantity': cart_item.product.quantity
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = quantity
            cart_item.save()

            return Response(CartItemSerializer(cart_item).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

        product_name = cart_item.product.name
        cart_item.delete()

        return Response(
            {'detail': f'Товар "{product_name}" удален из корзины'},
            status=status.HTTP_200_OK
        )
