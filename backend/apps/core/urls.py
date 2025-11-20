from django.urls import path
from .views import (
    import_products,
    export_products,
    check_import_status,
    system_status,
    upload_file,
    get_import_stats,
    cleanup_old_files,
    api_documentation
)

urlpatterns = [
    # Импорт/экспорт
    path('import-products/', import_products, name='import-products'),
    path('export-products/', export_products, name='export-products'),
    path('import-status/<str:task_id>/', check_import_status, name='import-status'),

    # Файлы
    path('upload-file/', upload_file, name='upload-file'),
    path('cleanup-files/', cleanup_old_files, name='cleanup-files'),

    # Статус и статистика
    path('system-status/', system_status, name='system-status'),
    path('import-stats/', get_import_stats, name='import-stats'),

    # Документация
    path('documentation/', api_documentation, name='api-documentation'),
]