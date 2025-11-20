from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(bind=True)
def debug_task(self):
    """Тестовая задача для проверки работы Celery"""
    print(f'Debug task executed: {self.request.id}')
    return f'Task {self.request.id} completed successfully'



@shared_task
def send_order_confirmation_email(order_id):
    """Отправка email подтверждения заказа клиенту"""
    try:
        from backend.apps.orders.models import Order  # Исправленный импорт
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)

        subject = f'Order Confirmation - #{order.order_number}'
        message = f"""
        Dear {order.user.first_name or order.user.username},

        Thank you for your order! Here are your order details:

        Order Number: {order.order_number}
        Total Amount: ${order.total_amount}
        Delivery Address: {order.delivery_address}

        Order Items:
        """

        for item in order.items.all():
            message += f"\n- {item.product.name} x {item.quantity}: ${item.total_price}"

        message += "\n\nWe will notify you when your order ships."

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )

        return f"Confirmation email sent for order #{order.order_number}"

    except Exception as e:
        return f"Error sending confirmation email: {str(e)}"


@shared_task
def send_order_to_admin(order_id):
    """Отправка уведомления о новом заказе администратору"""
    try:
        from backend.apps.orders.models import Order  # Исправленный импорт
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)

        subject = f'New Order Received - #{order.order_number}'
        message = f"""
        New order received:

        Order Number: {order.order_number}
        Customer: {order.user.email}
        Total Amount: ${order.total_amount}
        Delivery Address: {order.delivery_address}

        Order Items:
        """

        for item in order.items.all():
            message += f"\n- {item.product.name} x {item.quantity}: ${item.total_price} (Supplier: {item.supplier.name})"

        # В реальном приложении здесь должен быть email администратора
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@example.com')

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )

        return f"Admin notification sent for order #{order.order_number}"

    except Exception as e:
        return f"Error sending admin notification: {str(e)}"


@shared_task
def import_products_task(file_path):
    """Задача для импорта товаров"""
    try:
        from .import_export import ProductImporter
        importer = ProductImporter()
        result = importer.import_from_yaml(file_path)
        return {
            'status': 'success',
            'result': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }