from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
import os
import json
import redis
import psutil
import uuid
from datetime import datetime, timedelta

from .models import (
    SystemSettings, ImportJob, ExportJob, EmailTemplate,
    SystemLog, BackupSchedule, BackupRecord, APIRequestLog,
    Notification, SystemHealthCheck
)
from .serializers import (
    SystemSettingsSerializer, SystemSettingsUpdateSerializer,
    ImportJobSerializer, ImportJobCreateSerializer,
    ExportJobSerializer, ExportJobCreateSerializer,
    EmailTemplateSerializer, EmailTemplateCreateSerializer,
    SystemLogSerializer, SystemLogFilterSerializer,
    BackupScheduleSerializer, BackupRecordSerializer,
    APIRequestLogSerializer, APIRequestLogFilterSerializer,
    NotificationSerializer, NotificationCreateSerializer,
    MarkNotificationsReadSerializer, SystemHealthCheckSerializer,
    SystemStatusSerializer, ImportStatsSerializer, TaskStatusSerializer,
    FileUploadSerializer, CleanupFilesSerializer, SystemInfoSerializer,
    APIDocumentationSerializer
)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления системными настройками"""
    permission_classes = [IsAdminUser]
    queryset = SystemSettings.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SystemSettingsUpdateSerializer
        return SystemSettingsSerializer


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра задач импорта"""
    permission_classes = [IsAdminUser]
    queryset = ImportJob.objects.select_related('user').all()
    serializer_class = ImportJobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'user']


class ExportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра задач экспорта"""
    permission_classes = [IsAdminUser]
    queryset = ExportJob.objects.select_related('user').all()
    serializer_class = ExportJobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'user']


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet для управления шаблонами email"""
    permission_classes = [IsAdminUser]
    queryset = EmailTemplate.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return EmailTemplateCreateSerializer
        return EmailTemplateSerializer


class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра системных логов"""
    permission_classes = [IsAdminUser]
    queryset = SystemLog.objects.select_related('user').all()
    serializer_class = SystemLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['level', 'module', 'user']


class BackupScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления расписанием резервного копирования"""
    permission_classes = [IsAdminUser]
    queryset = BackupSchedule.objects.all()
    serializer_class = BackupScheduleSerializer


class BackupRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра записей резервного копирования"""
    permission_classes = [IsAdminUser]
    queryset = BackupRecord.objects.select_related('schedule').all()
    serializer_class = BackupRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['schedule', 'status']


class APIRequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра логов API запросов"""
    permission_classes = [IsAdminUser]
    queryset = APIRequestLog.objects.select_related('user').all()
    serializer_class = APIRequestLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['method', 'status_code', 'user']


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet для управления уведомлениями"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Отметить уведомления как прочитанные"""
        serializer = MarkNotificationsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notifications = self.get_queryset()

        if serializer.validated_data.get('mark_all'):
            updated = notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
            return Response({'message': f'{updated} notifications marked as read'})
        else:
            notification_ids = serializer.validated_data.get('notification_ids', [])
            updated = notifications.filter(id__in=notification_ids, is_read=False).update(
                is_read=True, read_at=timezone.now()
            )
            return Response({'message': f'{updated} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Получить количество непрочитанных уведомлений"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class SystemHealthCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра проверок здоровья системы"""
    permission_classes = [IsAdminUser]
    queryset = SystemHealthCheck.objects.all()
    serializer_class = SystemHealthCheckSerializer


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
        # Создаем запись ImportJob
        import_job = ImportJob.objects.create(
            user=request.user,
            file_path=file_path,
            status='pending'
        )

        # Запускаем асинхронную задачу
        result = import_products_task.delay(file_path)

        # Сохраняем task_id
        import_job.task_id = result.id
        import_job.save()

        return Response({
            'task_id': result.id,
            'import_job_id': import_job.id,
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
    supplier_id = request.data.get('supplier_id')

    # Убедимся, что файл имеет правильное расширение
    if not file_path.endswith(('.yaml', '.yml')):
        file_path += '.yaml'

    try:
        # Создаем запись ExportJob
        export_job = ExportJob.objects.create(
            user=request.user,
            file_path=file_path,
            status='pending'
        )

        # Запускаем асинхронную задачу
        if supplier_id:
            result = export_products_task.delay(file_path, supplier_id)
        else:
            result = export_products_task.delay(file_path)

        # Сохраняем task_id
        export_job.task_id = result.id
        export_job.save()

        return Response({
            'task_id': result.id,
            'export_job_id': export_job.id,
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

    serializer = SystemStatusSerializer(status_info)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_file(request):
    """Загрузка файла для импорта"""
    from django.core.files.storage import default_storage
    from django.conf import settings

    serializer = FileUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    file = serializer.validated_data['file']

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
    from backend.apps.products.models import Product, Category
    from backend.apps.suppliers.models import Supplier
    from backend.apps.orders.models import Order

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

    serializer = ImportStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def cleanup_old_files(request):
    """Очистка старых файлов импорта"""
    import glob
    from django.conf import settings

    serializer = CleanupFilesSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    days_old = serializer.validated_data['days']
    import_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
    export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')

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
            'supplier_products': 'GET /api/suppliers/my/products/ (supplier only)',
            'toggle_orders': 'POST /api/suppliers/my/toggle-orders/ (supplier only)',
            'supplier_orders': 'GET /api/suppliers/my/orders/ (supplier only)',
            'supplier_stats': 'GET /api/suppliers/my/stats/ (supplier only)',
        },
        'core': {
            'import_products': 'POST /api/core/import-products/ (admin only)',
            'export_products': 'POST /api/core/export-products/ (admin only)',
            'check_import_status': 'GET /api/core/import-status/{task_id}/ (admin only)',
            'system_status': 'GET /api/core/system-status/',
            'upload_file': 'POST /api/core/upload-file/ (admin only)',
            'import_stats': 'GET /api/core/import-stats/ (admin only)',
            'cleanup_files': 'POST /api/core/cleanup-files/ (admin only)',
            'system_settings': 'GET /api/core/system-settings/ (admin only)',
            'notifications': 'GET /api/core/notifications/ (user only)',
        }
    }

    serializer = APIDocumentationSerializer(docs)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_info(request):
    """Информация о системе"""
    import django
    import sys
    from django.contrib.auth import get_user_model

    User = get_user_model()

    info = {
        'django_version': django.get_version(),
        'python_version': sys.version,
        'database_backend': settings.DATABASES['default']['ENGINE'],
        'debug_mode': settings.DEBUG,
        'installed_apps_count': len(settings.INSTALLED_APPS),
        'total_users': User.objects.count(),
        'total_products': 0,
        'total_orders': 0,
    }

    # Безопасно получаем статистику по другим моделям
    try:
        from backend.apps.products.models import Product
        info['total_products'] = Product.objects.count()
    except:
        info['total_products'] = 'N/A'

    try:
        from backend.apps.orders.models import Order
        info['total_orders'] = Order.objects.count()
    except:
        info['total_orders'] = 'N/A'

    serializer = SystemInfoSerializer(info)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def run_health_check(request):
    """Запуск проверки здоровья системы"""
    from .tasks import debug_task

    try:
        # Запускаем тестовую задачу Celery
        result = debug_task.delay()

        # Обновляем или создаем запись SystemHealthCheck
        service_name = "Celery Worker"
        health_check, created = SystemHealthCheck.objects.get_or_create(
            service_name=service_name
        )

        if result.ready():
            health_check.status = True
            health_check.response_time = 0.1  # Примерное время
            health_check.error_message = ""
        else:
            health_check.status = False
            health_check.error_message = "Celery task not completed"

        health_check.save()

        return Response({
            'message': 'Health check completed',
            'celery_status': 'running' if not result.ready() else 'completed'
        })

    except Exception as e:
        return Response(
            {'error': f'Health check failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_recent_activity(request):
    """Получение последней активности системы"""
    # Последние логи
    recent_logs = SystemLog.objects.order_by('-created_at')[:10]
    log_serializer = SystemLogSerializer(recent_logs, many=True)

    # Последние задачи импорта/экспорта
    recent_imports = ImportJob.objects.order_by('-created_at')[:5]
    import_serializer = ImportJobSerializer(recent_imports, many=True)

    recent_exports = ExportJob.objects.order_by('-created_at')[:5]
    export_serializer = ExportJobSerializer(recent_exports, many=True)

    return Response({
        'recent_logs': log_serializer.data,
        'recent_imports': import_serializer.data,
        'recent_exports': export_serializer.data,
    })