from django.contrib import admin
from apps.core.models import (
    SystemSettings, ImportJob, ExportJob, EmailTemplate,
    SystemLog, BackupSchedule, BackupRecord, APIRequestLog,
    Notification, SystemHealthCheck
)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'updated_at')
    list_editable = ('value',)
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_count', 'updated_count', 'error_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('file_path', 'user__email')
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'task_id')

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'file_path', 'status', 'task_id')
        }),
        ('Statistics', {
            'fields': ('total_processed', 'created_count', 'updated_count', 'error_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Errors', {
            'fields': ('error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_exported', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('file_path', 'user__email')
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'task_id')


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'updated_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'subject')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('level', 'module', 'message_short', 'user', 'created_at')
    list_filter = ('level', 'module', 'created_at')
    search_fields = ('message', 'user__email')
    readonly_fields = ('created_at',)

    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_type', 'frequency', 'is_active', 'last_run', 'next_run')
    list_filter = ('backup_type', 'frequency', 'is_active')
    search_fields = ('name',)


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'status', 'file_size_mb', 'duration', 'created_at')
    list_filter = ('status', 'schedule', 'created_at')
    readonly_fields = ('created_at', 'completed_at')

    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = 'File Size'


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ('method', 'path_short', 'status_code', 'user', 'response_time', 'created_at')
    list_filter = ('method', 'status_code', 'created_at')
    search_fields = ('path', 'user__email')
    readonly_fields = ('created_at',)

    def path_short(self, obj):
        return obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
    path_short.short_description = 'Path'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('created_at', 'read_at')


@admin.register(SystemHealthCheck)
class SystemHealthCheckAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'status', 'response_time', 'last_check')
    list_filter = ('status', 'last_check')
    readonly_fields = ('last_check',)
