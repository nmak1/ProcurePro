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
        from backend.apps.orders.models import Order
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
        from backend.apps.orders.models import Order
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
    """Задача для импорта товаров из YAML файла"""
    try:
        from .import_export import ProductImporter
        importer = ProductImporter()
        result = importer.import_from_yaml(file_path)
        return {
            'status': 'success',
            'result': result,
            'message': f"Import completed: {result['created']} created, {result['updated']} updated, {result['errors']} errors"
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Import failed: {str(e)}"
        }


@shared_task
def export_products_task(file_path):
    """Задача для экспорта товаров в YAML файл"""
    try:
        from .import_export import ProductExporter
        exporter = ProductExporter()
        result = exporter.export_to_yaml(file_path)
        return {
            'status': 'success',
            'result': result,
            'message': 'Export completed successfully'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Export failed: {str(e)}"
        }


@shared_task
def send_notification_email(user_id, subject, message):
    """Отправка уведомления по email"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=user_id)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Notification email sent to {user.email}"

    except Exception as e:
        return f"Error sending notification email: {str(e)}"


@shared_task
def cleanup_old_files_task(days_old=7):
    """Очистка старых файлов импорта/экспорта"""
    import os
    import glob
    from datetime import datetime, timedelta
    from django.conf import settings

    try:
        import_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')

        cutoff_time = datetime.now() - timedelta(days=days_old)
        deleted_files = []
        error_files = []

        # Очищаем файлы импорта
        if os.path.exists(import_dir):
            for file_path in glob.glob(os.path.join(import_dir, '*.yaml')) + glob.glob(
                    os.path.join(import_dir, '*.yml')):
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_files.append(os.path.basename(file_path))
                except Exception as e:
                    error_files.append({
                        'file': os.path.basename(file_path),
                        'error': str(e)
                    })

        # Очищаем файлы экспорта
        if os.path.exists(export_dir):
            for file_path in glob.glob(os.path.join(export_dir, '*.yaml')) + glob.glob(
                    os.path.join(export_dir, '*.yml')):
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_files.append(os.path.basename(file_path))
                except Exception as e:
                    error_files.append({
                        'file': os.path.basename(file_path),
                        'error': str(e)
                    })

        return {
            'status': 'success',
            'deleted_files': deleted_files,
            'error_files': error_files,
            'total_deleted': len(deleted_files),
            'total_errors': len(error_files),
            'message': f"Cleanup completed: {len(deleted_files)} files deleted, {len(error_files)} errors"
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Cleanup failed: {str(e)}"
        }


@shared_task
def generate_backup_task(backup_type='database'):
    """Создание резервной копии"""
    import os
    import subprocess
    from datetime import datetime
    from django.conf import settings

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')

        # Создаем директорию для бэкапов если не существует
        os.makedirs(backup_dir, exist_ok=True)

        if backup_type == 'database':
            # Бэкап базы данных SQLite
            db_path = settings.DATABASES['default']['NAME']
            backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')

            import shutil
            shutil.copy2(db_path, backup_path)

            return {
                'status': 'success',
                'backup_path': backup_path,
                'backup_type': 'database',
                'message': 'Database backup created successfully'
            }

        elif backup_type == 'media':
            # Бэкап медиа файлов
            media_backup_path = os.path.join(backup_dir, f'media_backup_{timestamp}.zip')

            import zipfile
            with zipfile.ZipFile(media_backup_path, 'w') as zipf:
                for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, settings.MEDIA_ROOT)
                        zipf.write(file_path, arcname)

            return {
                'status': 'success',
                'backup_path': media_backup_path,
                'backup_type': 'media',
                'message': 'Media files backup created successfully'
            }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Backup failed: {str(e)}"
        }