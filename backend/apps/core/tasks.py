from celery import shared_task
from django.apps import apps
from django.core.mail import send_mail
from django.conf import settings
from django.db import models  # ДОБАВЛЕНО: импорт models


@shared_task(bind=True)
def debug_task(self):
    """Тестовая задача для проверки работы Celery"""
    print(f'Debug task executed: {self.request.id}')
    return f'Task {self.request.id} completed successfully'


@shared_task
def send_order_confirmation_email(order_id):
    """Отправка email подтверждения заказа клиенту"""
    try:
        # ИСПРАВЛЕНО: используем apps.get_model вместо импорта
        Order = apps.get_model('orders', 'Order')
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)

        subject = f'Подтверждение заказа - #{order.id}'
        message = f"""
        Уважаемый(ая) {order.user.first_name or order.user.username},

        Благодарим за ваш заказ! Детали заказа:

        Номер заказа: #{order.id}
        Общая сумма: {order.total_amount} руб.
        Адрес доставки: {order.shipping_address}

        Состав заказа:
        """

        for item in order.items.all():
            message += f"\n- {item.product.name} x {item.quantity}: {item.total_price} руб."

        message += "\n\nМы уведомим вас, когда заказ будет отправлен."

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )

        return f"Письмо с подтверждением отправлено для заказа #{order.id}"

    except Exception as e:
        return f"Ошибка отправки письма с подтверждением: {str(e)}"


@shared_task
def send_order_to_admin(order_id):
    """Отправка уведомления о новом заказе администратору"""
    try:
        # ИСПРАВЛЕНО: используем apps.get_model вместо импорта
        Order = apps.get_model('orders', 'Order')
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)

        subject = f'Новый заказ - #{order.id}'
        message = f"""
        Поступил новый заказ:

        Номер заказа: #{order.id}
        Клиент: {order.user.email}
        Общая сумма: {order.total_amount} руб.
        Адрес доставки: {order.shipping_address}

        Состав заказа:
        """

        for item in order.items.all():
            message += f"\n- {item.product.name} x {item.quantity}: {item.total_price} руб."

        # Получаем email администраторов
        User = apps.get_model('users', 'User')
        admin_emails = User.objects.filter(
            user_type='admin',
            is_active=True
        ).values_list('email', flat=True)

        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                fail_silently=False,
            )

        return f"Уведомление администратору отправлено для заказа #{order.id}"

    except Exception as e:
        return f"Ошибка отправки уведомления администратору: {str(e)}"


@shared_task
def import_products_task(file_path):
    """Задача для импорта товаров из YAML файла"""
    try:
        from .import_export import ProductImporter
        importer = ProductImporter()
        result = importer.import_from_file(file_path)
        return {
            'status': 'success',
            'result': result,
            'message': 'Импорт завершен успешно'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Ошибка импорта: {str(e)}"
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
            'message': 'Экспорт завершен успешно'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Ошибка экспорта: {str(e)}"
        }


@shared_task
def send_notification_email(user_id, subject, message):
    """Отправка уведомления по email"""
    try:
        User = apps.get_model('users', 'User')
        user = User.objects.get(id=user_id)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Уведомление отправлено на {user.email}"

    except Exception as e:
        return f"Ошибка отправки уведомления: {str(e)}"


@shared_task
def cleanup_old_files_task(days_old=7):
    """Очистка старых файлов импорта/экспорта"""
    import os
    import glob
    from datetime import datetime, timedelta

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
            'message': f"Очистка завершена: {len(deleted_files)} файлов удалено, {len(error_files)} ошибок"
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Ошибка очистки: {str(e)}"
        }


@shared_task
def generate_backup_task(backup_type='database'):
    """Создание резервной копии"""
    import os
    from datetime import datetime

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
                'message': 'Резервная копия базы данных создана успешно'
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
                'message': 'Резервная копия медиа файлов создана успешно'
            }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Ошибка создания резервной копии: {str(e)}"
        }


@shared_task
def update_product_availability():
    """Периодическая задача для обновления доступности товаров"""
    try:
        Product = apps.get_model('products', 'Product')

        # Находим товары, которые должны быть недоступны
        products_to_disable = Product.objects.filter(
            quantity__lt=models.F('min_quantity'),  # ТЕПЕРЬ models импортирован
            is_available=True
        )

        disabled_count = products_to_disable.update(is_available=False)

        # Находим товары, которые должны быть доступны
        products_to_enable = Product.objects.filter(
            quantity__gte=models.F('min_quantity'),  # ТЕПЕРЬ models импортирован
            is_available=False
        )

        enabled_count = products_to_enable.update(is_available=True)

        return {
            'status': 'success',
            'disabled_count': disabled_count,
            'enabled_count': enabled_count,
            'message': f'Обновлено доступности: отключено {disabled_count}, включено {enabled_count} товаров'
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f'Ошибка обновления доступности товаров: {str(e)}'
        }


@shared_task
def send_daily_sales_report():
    """Ежедневный отчет о продажах"""
    try:
        from datetime import datetime, timedelta
        Order = apps.get_model('orders', 'Order')
        OrderItem = apps.get_model('orders', 'OrderItem')

        # Данные за последние 24 часа
        yesterday = datetime.now() - timedelta(days=1)

        # Статистика заказов
        total_orders = Order.objects.filter(created_at__gte=yesterday).count()
        completed_orders = Order.objects.filter(
            created_at__gte=yesterday,
            status='delivered'
        ).count()

        # Сумма продаж
        total_sales = Order.objects.filter(
            created_at__gte=yesterday,
            status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0

        # Популярные товары
        popular_products = OrderItem.objects.filter(
            order__created_at__gte=yesterday
        ).values(
            'product__name'
        ).annotate(
            total_sold=models.Sum('quantity')
        ).order_by('-total_sold')[:5]

        # Формируем отчет
        subject = f'Ежедневный отчет о продажах - {datetime.now().strftime("%d.%m.%Y")}'
        message = f"""
        Ежедневный отчет о продажах:

        Период: последние 24 часа
        Всего заказов: {total_orders}
        Завершенных заказов: {completed_orders}
        Общая сумма продаж: {total_sales} руб.

        Популярные товары:
        """

        for product in popular_products:
            message += f"\n- {product['product__name']}: {product['total_sold']} шт."

        # Отправляем администраторам
        User = apps.get_model('users', 'User')
        admin_emails = User.objects.filter(
            user_type='admin',
            is_active=True
        ).values_list('email', flat=True)

        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                fail_silently=False,
            )

        return {
            'status': 'success',
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'total_sales': total_sales,
            'message': 'Ежедневный отчет отправлен'
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': f'Ошибка отправки ежедневного отчета: {str(e)}'
        }
