from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from apps.orders.models import Order, OrderItem
from apps.orders.serializers import (
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items', 'items__product'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """Создание заказа из корзины"""
        try:
            with transaction.atomic():
                # Получаем корзину пользователя
                from apps.cart.models import Cart
                cart = Cart.objects.get(user=request.user)
                cart_items = cart.items.select_related('product').all()

                if not cart_items:
                    return Response(
                        {'error': 'Корзина пуста'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Проверяем доступность товаров
                unavailable_products = []
                for item in cart_items:
                    if not item.product.is_available or item.product.quantity < item.quantity:
                        unavailable_products.append(item.product.name)

                if unavailable_products:
                    return Response(
                        {'error': f'Некоторые товары недоступны: {", ".join(unavailable_products)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Создаем заказ
                order_serializer = self.get_serializer(data=request.data)
                order_serializer.is_valid(raise_exception=True)
                order = order_serializer.save()

                # Создаем элементы заказа
                total_amount = 0
                for cart_item in cart_items:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )
                    total_amount += order_item.total_price

                    # Обновляем количество товара на складе
                    cart_item.product.quantity -= cart_item.quantity
                    cart_item.product.save()

                # Обновляем общую сумму заказа
                order.total_amount = total_amount
                order.save()

                # Очищаем корзину
                cart.items.all().delete()

                # Отправляем email уведомления (асинхронно через Celery)
                self._send_order_emails_async(order.id)

                serializer = OrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Cart.DoesNotExist:
            return Response(
                {'error': 'Корзина не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Ошибка создания заказа: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _send_order_emails_async(self, order_id):
        """Асинхронная отправка email уведомлений через Celery"""
        try:
            from apps.core.tasks import send_order_confirmation_email, send_order_to_admin
            send_order_confirmation_email.delay(order_id)
            send_order_to_admin.delay(order_id)
        except Exception as e:
            # Логируем ошибку, но не прерываем создание заказа
            print(f"Ошибка отправки email: {e}")

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Обновление статуса заказа"""
        order = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'order': order})
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        old_status = order.status

        order.status = new_status
        order.save()

        # Отправляем уведомление при изменении статуса
        if old_status != new_status:
            self._send_status_update_email(order)

        return Response(OrderSerializer(order).data)

    def _send_status_update_email(self, order):
        """Отправка email об изменении статуса заказа"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            subject = f'Статус заказа #{order.id} изменен'
            message = f"""
            Статус вашего заказа #{order.id} изменен на: {order.get_status_display()}

            Текущий статус: {order.get_status_display()}
            Сумма заказа: {order.total_amount} руб.
            Адрес доставки: {order.shipping_address}

            Спасибо, что выбрали наш магазин!
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Ошибка отправки email о смене статуса: {e}")

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика заказов пользователя"""
        orders = self.get_queryset()

        stats = {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='pending').count(),
            'completed_orders': orders.filter(status='delivered').count(),
            'total_spent': sum(order.total_amount for order in orders if order.total_amount),
        }

        return Response(stats)
