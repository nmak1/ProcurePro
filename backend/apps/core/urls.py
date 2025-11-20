from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    import_products, export_products, check_import_status,
    system_status, upload_file, get_import_stats,
    cleanup_old_files, api_documentation,
    SystemSettingsViewSet, ImportJobViewSet, ExportJobViewSet,
    EmailTemplateViewSet, SystemLogViewSet, BackupScheduleViewSet,
    BackupRecordViewSet, APIRequestLogViewSet, NotificationViewSet,
    SystemHealthCheckViewSet
)

router = DefaultRouter()
router.register(r'system-settings', SystemSettingsViewSet)
router.register(r'import-jobs', ImportJobViewSet)
router.register(r'export-jobs', ExportJobViewSet)
router.register(r'email-templates', EmailTemplateViewSet)
router.register(r'system-logs', SystemLogViewSet)
router.register(r'backup-schedules', BackupScheduleViewSet)
router.register(r'backup-records', BackupRecordViewSet)
router.register(r'api-logs', APIRequestLogViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'health-checks', SystemHealthCheckViewSet)

urlpatterns = [
    # API endpoints
    path('import-products/', import_products, name='import-products'),
    path('export-products/', export_products, name='export-products'),
    path('import-status/<str:task_id>/', check_import_status, name='import-status'),
    path('upload-file/', upload_file, name='upload-file'),
    path('cleanup-files/', cleanup_old_files, name='cleanup-files'),
    path('system-status/', system_status, name='system-status'),
    path('import-stats/', get_import_stats, name='import-stats'),
    path('documentation/', api_documentation, name='api-documentation'),

    # Router URLs
    path('', include(router.urls)),
]