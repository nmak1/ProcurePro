from rest_framework import serializers
from django.utils import timezone
from .models import (
    SystemSettings, ImportJob, ExportJob, EmailTemplate,
    SystemLog, BackupSchedule, BackupRecord, APIRequestLog,
    Notification, SystemHealthCheck
)


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор для системных настроек"""

    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'updated_at']
        read_only_fields = ['updated_at']


class SystemSettingsUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления системных настроек"""

    class Meta:
        model = SystemSettings
        fields = ['value', 'description']


class ImportJobSerializer(serializers.ModelSerializer):
    """Сериализатор для задач импорта"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = [
            'id', 'user', 'user_email', 'file_path', 'status', 'task_id',
            'total_processed', 'created_count', 'updated_count', 'error_count',
            'error_message', 'started_at', 'completed_at', 'created_at', 'duration'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'status', 'task_id', 'total_processed',
            'created_count', 'updated_count', 'error_count', 'error_message',
            'started_at', 'completed_at', 'created_at', 'duration'
        ]

    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return str(obj.completed_at - obj.started_at)
        return None


class ImportJobCreateSerializer(serializers.Serializer):
    """Сериализатор для создания задачи импорта"""
    file_path = serializers.CharField(max_length=500)

    def validate_file_path(self, value):
        import os
        if not os.path.exists(value):
            raise serializers.ValidationError("File does not exist")
        if not value.endswith(('.yaml', '.yml')):
            raise serializers.ValidationError("File must be YAML format (.yaml or .yml)")
        return value


class ExportJobSerializer(serializers.ModelSerializer):
    """Сериализатор для задач экспорта"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    duration = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = ExportJob
        fields = [
            'id', 'user', 'user_email', 'file_path', 'status', 'task_id',
            'total_exported', 'error_message', 'started_at', 'completed_at',
            'created_at', 'duration', 'file_size'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'status', 'task_id', 'total_exported',
            'error_message', 'started_at', 'completed_at', 'created_at', 'duration'
        ]

    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return str(obj.completed_at - obj.started_at)
        return None

    def get_file_size(self, obj):
        import os
        if obj.file_path and os.path.exists(obj.file_path):
            size = os.path.getsize(obj.file_path)
            # Конвертируем в читаемый формат
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
        return None


class ExportJobCreateSerializer(serializers.Serializer):
    """Сериализатор для создания задачи экспорта"""
    file_path = serializers.CharField(max_length=500, required=False)
    supplier_id = serializers.IntegerField(required=False)

    def validate_file_path(self, value):
        if value and not value.endswith(('.yaml', '.yml')):
            raise serializers.ValidationError("File must have .yaml or .yml extension")
        return value


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор для шаблонов email"""

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'body',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EmailTemplateCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания шаблона email"""

    class Meta:
        model = EmailTemplate
        fields = ['name', 'template_type', 'subject', 'body', 'is_active']


class SystemLogSerializer(serializers.ModelSerializer):
    """Сериализатор для системных логов"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = SystemLog
        fields = [
            'id', 'level', 'module', 'message', 'user', 'user_email',
            'ip_address', 'user_agent', 'object_id', 'object_type', 'created_at'
        ]
        read_only_fields = ['created_at']


class SystemLogFilterSerializer(serializers.Serializer):
    """Сериализатор для фильтрации логов"""
    level = serializers.ChoiceField(choices=SystemLog.LEVEL_CHOICES, required=False)
    module = serializers.ChoiceField(choices=SystemLog.MODULE_CHOICES, required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    user_id = serializers.IntegerField(required=False)


class BackupScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания резервного копирования"""
    last_run_status = serializers.SerializerMethodField()

    class Meta:
        model = BackupSchedule
        fields = [
            'id', 'name', 'backup_type', 'frequency', 'is_active',
            'keep_backups', 'include_media', 'compress_backup',
            'scheduled_time', 'last_run', 'next_run',
            'notify_on_success', 'notify_on_failure', 'notification_email',
            'created_at', 'updated_at', 'last_run_status'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_run', 'next_run']

    def get_last_run_status(self, obj):
        last_backup = obj.backups.order_by('-created_at').first()
        return last_backup.status if last_backup else 'never_run'


class BackupRecordSerializer(serializers.ModelSerializer):
    """Сериализатор для записей резервного копирования"""
    schedule_name = serializers.CharField(source='schedule.name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = BackupRecord
        fields = [
            'id', 'schedule', 'schedule_name', 'status', 'file_path',
            'file_size', 'file_size_mb', 'duration', 'error_message',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'completed_at']

    def get_file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return None


class APIRequestLogSerializer(serializers.ModelSerializer):
    """Сериализатор для логов API запросов"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = APIRequestLog
        fields = [
            'id', 'user', 'user_email', 'method', 'path', 'query_params',
            'status_code', 'response_time', 'ip_address', 'user_agent',
            'request_body', 'response_body', 'created_at'
        ]
        read_only_fields = ['created_at']


class APIRequestLogFilterSerializer(serializers.Serializer):
    """Сериализатор для фильтрации логов API"""
    method = serializers.ChoiceField(choices=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], required=False)
    status_code = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    user_id = serializers.IntegerField(required=False)
    path_contains = serializers.CharField(required=False)


class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор для уведомлений"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_email', 'type', 'title', 'message',
            'is_read', 'object_id', 'object_type', 'created_at', 'read_at'
        ]
        read_only_fields = ['created_at', 'read_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания уведомлений"""

    class Meta:
        model = Notification
        fields = ['user', 'type', 'title', 'message', 'object_id', 'object_type']


class MarkNotificationsReadSerializer(serializers.Serializer):
    """Сериализатор для отметки уведомлений как прочитанных"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)


class SystemHealthCheckSerializer(serializers.ModelSerializer):
    """Сериализатор для проверки здоровья системы"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SystemHealthCheck
        fields = [
            'id', 'service_name', 'status', 'status_display',
            'response_time', 'error_message', 'last_check'
        ]
        read_only_fields = ['last_check']


class SystemStatusSerializer(serializers.Serializer):
    """Сериализатор для статуса системы"""
    database = serializers.CharField()
    cache = serializers.CharField()
    celery = serializers.CharField()
    storage = serializers.DictField()
    memory_usage = serializers.DictField()


class ImportStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики импорта"""
    products = serializers.DictField()
    categories = serializers.DictField()
    suppliers = serializers.DictField()
    orders = serializers.DictField()


class TaskStatusSerializer(serializers.Serializer):
    """Сериализатор для статуса задачи"""
    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class FileUploadSerializer(serializers.Serializer):
    """Сериализатор для загрузки файлов"""
    file = serializers.FileField()

    def validate_file(self, value):
        import os
        valid_extensions = ['.yaml', '.yml']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError(
                f"Unsupported file extension. Supported extensions: {', '.join(valid_extensions)}"
            )
        return value


class CleanupFilesSerializer(serializers.Serializer):
    """Сериализатор для очистки файлов"""
    days = serializers.IntegerField(min_value=1, max_value=365, default=7)


class SystemInfoSerializer(serializers.Serializer):
    """Сериализатор для информации о системе"""
    django_version = serializers.CharField()
    python_version = serializers.CharField()
    database_backend = serializers.CharField()
    debug_mode = serializers.BooleanField()
    installed_apps_count = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()


class APIDocumentationSerializer(serializers.Serializer):
    """Сериализатор для документации API"""
    authentication = serializers.DictField()
    products = serializers.DictField()
    cart = serializers.DictField()
    orders = serializers.DictField()
    suppliers = serializers.DictField()
    core = serializers.DictField()