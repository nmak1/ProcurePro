from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
import os
import json


@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_products(request):
    """API endpoint для импорта товаров из YAML файла"""
    from .tasks import import_products_task

    file_path = request.data.get('file_path')
    if not file_path:
        return Response(
            {'error': 'file_path is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Проверяем существование файла
    if not os.path.exists(file_path):
        return Response(
            {'error': f'File not found: {file_path}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Проверяем расширение файла
    if not file_path.endswith(('.yaml', '.yml')):
        return Response(
            {'error': 'File must be YAML format (.yaml or .yml)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Запускаем асинхронную задачу
        result = import_products_task.delay(file_path)
        return Response({
            'task_id': result.id,
            'message': 'Import started successfully',
            'file_path': file_path,
            'status': 'processing'
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def export_products(request):
    """API endpoint для экспорта товаров в YAML файл"""
    from .tasks import export_products_task

    file_path = request.data.get('file_path', 'products_export.yaml')

    # Убедимся, что файл имеет правильное расширение
    if not file_path.endswith(('.yaml', '.yml')):
        file_path += '.yaml'

    try:
        # Запускаем асинхронную задачу
        result = export_products_task.delay(file_path)
        return Response({
            'task_id': result.id,
            'message': 'Export started successfully',
            'file_path': file_path,
            'status': 'processing'
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def check_import_status(request, task_id):
    """Проверка статуса задачи импорта/экспорта"""
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id)

    response_data = {
        'task_id': task_id,
        'status': task_result.status,
    }

    if task_result.ready():
        if task_result.successful():
            response_data['result'] = task_result.result
            response_data['status'] = 'completed'
        else:
            response_data['error'] = str(task_result.result)
            response_data['status'] = 'failed'

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """Проверка статуса системы"""
    from django.db import connection
    from django.core.cache import cache
    import redis
    import psutil
    import os

    status_info = {
        'database': 'unknown',
        'cache': 'unknown',
        'celery': 'unknown',
        'storage': 'unknown',
        'memory_usage': 'unknown'
    }

    # Проверка базы данных
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status_info['database'] = 'connected'
    except Exception as e:
        status_info['database'] = f'error: {str(e)}'

    # Проверка кеша (Redis)
    try:
        cache.set('health_check', 'ok', 5)
        if cache.get('health_check') == 'ok':
            status_info['cache'] = 'connected'
        else:
            status_info['cache'] = 'error'
    except Exception as e:
        status_info['cache'] = f'error: {str(e)}'

    # Проверка Celery
    try:
        from .tasks import debug_task
        result = debug_task.delay()
        if result.ready():
            status_info['celery'] = 'connected'
        else:
            status_info['celery'] = 'processing'
    except Exception as e:
        status_info['celery'] = f'error: {str(e)}'

    # Проверка места на диске
    try:
        disk_usage = psutil.disk_usage('/')
        status_info['storage'] = {
            'total_gb': round(disk_usage.total / (1024 ** 3), 2),
            'used_gb': round(disk_usage.used / (1024 ** 3), 2),
            'free_gb': round(disk_usage.free / (1024 ** 3), 2),
            'percent_used': disk_usage.percent
        }
    except Exception:
        status_info['storage'] = 'unavailable'

    # Использование памяти
    try:
        memory = psutil.virtual_memory()
        status_info['memory_usage'] = {
            'total_gb': round(memory.total / (1024 ** 3), 2),
            'used_gb': round(memory.used / (1024 ** 3), 2),
            'percent_used': memory.percent
        }
    except Exception:
        status_info['memory_usage'] = 'unavailable'

    return Response(status_info)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_file(request):
    """Загрузка файла для импорта"""
    from django.core.files.storage import default_storage
    from django.conf import settings
    import uuid

    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    file = request.FILES['file']

    # Проверяем тип файла
    if not file.name.endswith(('.yaml', '.yml')):
        return Response(
            {'error': 'File must be YAML format (.yaml or .yml)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Генерируем уникальное имя файла
    file_extension = file.name.split('.')[-1]
    unique_filename = f"import_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = os.path.join(settings.MEDIA_ROOT, 'imports', unique_filename)

    # Сохраняем файл
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return Response({
            'message': 'File uploaded successfully',
            'file_path': file_path,
            'filename': unique_filename
        })

    except Exception as e:
        return Response(
            {'error': f'Failed to upload file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_import_stats(request):
    """Получение статистики импорта"""
    from products.models import Product, Category
    from suppliers.models import Supplier
    from orders.models import Order

    stats = {
        'products': {
            'total': Product.objects.count(),
            'available': Product.objects.filter(is_available=True).count(),
            'unavailable': Product.objects.filter(is_available=False).count(),
        },
        'categories': {
            'total': Category.objects.count(),
        },
        'suppliers': {
            'total': Supplier.objects.count(),
            'active': Supplier.objects.filter(is_active=True).count(),
            'accepting_orders': Supplier.objects.filter(accepts_orders=True).count(),
        },
        'orders': {
            'total': Order.objects.count(),
            'pending': Order.objects.filter(status='pending').count(),
            'completed': Order.objects.filter(status='delivered').count(),
        }
    }

    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def cleanup_old_files(request):
    """Очистка старых файлов импорта"""
    import glob
    from datetime import datetime, timedelta
    from django.conf import settings

    days_old = request.data.get('days', 7)  # По умолчанию 7 дней
    import_dir = os.path.join(settings.MEDIA_ROOT, 'imports')

    if not os.path.exists(import_dir):
        return Response({'message': 'Import directory does not exist'})

    # Находим все файлы старше указанного количества дней
    cutoff_time = datetime.now() - timedelta(days=days_old)
    deleted_files = []
    error_files = []

    for file_path in glob.glob(os.path.join(import_dir, '*.yaml')) + glob.glob(os.path.join(import_dir, '*.yml')):
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

    return Response({
        'deleted_files': deleted_files,
        'error_files': error_files,
        'total_deleted': len(deleted_files),
        'total_errors': len(error_files)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_documentation(request):
    """Документация API"""
    docs = {
        'authentication': {
            'login': 'POST /api/auth/login/',
            'register': 'POST /api/auth/register/',
            'profile': 'GET /api/auth/profile/',
        },
        'products': {
            'list_products': 'GET /api/products/products/',
            'product_detail': 'GET /api/products/products/{id}/',
            'list_categories': 'GET /api/products/categories/',
            'category_products': 'GET /api/products/categories/{id}/products/',
        },
        'cart': {
            'get_cart': 'GET /api/cart/cart/',
            'add_to_cart': 'POST /api/cart/cart/add_item/',
            'remove_from_cart': 'DELETE /api/cart/cart/remove_item/{item_id}/',
            'clear_cart': 'POST /api/cart/cart/clear/',
        },
        'orders': {
            'list_orders': 'GET /api/orders/orders/',
            'create_order': 'POST /api/orders/orders/',
            'order_detail': 'GET /api/orders/orders/{id}/',
            'delivery_addresses': 'GET /api/orders/delivery-addresses/',
        },
        'suppliers': {
            'supplier_products': 'GET /api/suppliers/products/ (supplier only)',
            'toggle_orders': 'POST /api/suppliers/toggle-orders/ (supplier only)',
        },
        'core': {
            'import_products': 'POST /api/core/import-products/ (admin only)',
            'export_products': 'POST /api/core/export-products/ (admin only)',
            'check_import_status': 'GET /api/core/import-status/{task_id}/ (admin only)',
            'system_status': 'GET /api/core/system-status/',
            'upload_file': 'POST /api/core/upload-file/ (admin only)',
            'import_stats': 'GET /api/core/import-stats/ (admin only)',
        }
    }

    return Response(docs)