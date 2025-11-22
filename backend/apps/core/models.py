from django.db import models
from django.conf import settings
from django.utils import timezone


class SystemSettings(models.Model):
    """Настройки системы"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"{self.key} = {self.value}"


class ImportJob(models.Model):
    """Задача импорта товаров"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='import_jobs')
    file_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=100, blank=True, null=True)

    # Статистика
    total_processed = models.IntegerField(default=0)
    created_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    # Ошибки
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)

    # Временные метки
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Import Job'
        verbose_name_plural = 'Import Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Import #{self.id} - {self.status}"


class ExportJob(models.Model):
    """Задача экспорта товаров"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='export_jobs')
    file_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=100, blank=True, null=True)

    # Статистика
    total_exported = models.IntegerField(default=0)

    # Ошибки
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)

    # Временные метки
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Export Job'
        verbose_name_plural = 'Export Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Export #{self.id} - {self.status}"


class EmailTemplate(models.Model):
    """Шаблоны email сообщений"""
    TEMPLATE_TYPES = [
        ('order_confirmation', 'Order Confirmation'),
        ('order_status_update', 'Order Status Update'),
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
        ('admin_notification', 'Admin Notification'),
    ]

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class SystemLog(models.Model):
    """Логи системы"""
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]

    MODULE_CHOICES = [
        ('import', 'Import'),
        ('export', 'Export'),
        ('orders', 'Orders'),
        ('users', 'Users'),
        ('products', 'Products'),
        ('system', 'System'),
        ('email', 'Email'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    module = models.CharField(max_length=20, choices=MODULE_CHOICES, default='system')
    message = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Дополнительные данные
    object_id = models.IntegerField(null=True, blank=True)
    object_type = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['level']),
            models.Index(fields=['module']),
        ]

    def __str__(self):
        return f"{self.level.upper()} - {self.module} - {self.message[:50]}"


class BackupSchedule(models.Model):
    """Расписание резервного копирования"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    BACKUP_TYPES = [
        ('database', 'Database'),
        ('media', 'Media Files'),
        ('full', 'Full Backup'),
    ]

    name = models.CharField(max_length=100)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)

    # Настройки
    keep_backups = models.IntegerField(default=30, help_text="Number of backups to keep")
    include_media = models.BooleanField(default=False)
    compress_backup = models.BooleanField(default=True)

    # Время выполнения
    scheduled_time = models.TimeField(default='02:00')
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)

    # Уведомления
    notify_on_success = models.BooleanField(default=False)
    notify_on_failure = models.BooleanField(default=True)
    notification_email = models.EmailField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Backup Schedule'
        verbose_name_plural = 'Backup Schedules'

    def __str__(self):
        return f"{self.name} ({self.backup_type})"


class BackupRecord(models.Model):
    """Запись о резервной копии"""
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    schedule = models.ForeignKey(BackupSchedule, on_delete=models.CASCADE, related_name='backups')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")

    # Статистика
    duration = models.DurationField(null=True, blank=True)

    # Ошибки
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Backup Record'
        verbose_name_plural = 'Backup Records'
        ordering = ['-created_at']

    def __str__(self):
        return f"Backup #{self.id} - {self.status}"


class APIRequestLog(models.Model):
    """Лог API запросов"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    query_params = models.TextField(blank=True)
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in seconds")
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # Request/Response данные
    request_body = models.TextField(blank=True, null=True)
    response_body = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'API Request Log'
        verbose_name_plural = 'API Request Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['method']),
            models.Index(fields=['status_code']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"


class Notification(models.Model):
    """Уведомления для пользователей"""
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    # Ссылка на связанный объект
    object_id = models.IntegerField(null=True, blank=True)
    object_type = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class SystemHealthCheck(models.Model):
    """Результаты проверки здоровья системы"""
    service_name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    response_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    last_check = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'System Health Check'
        verbose_name_plural = 'System Health Checks'

    def __str__(self):
        status = "Healthy" if self.status else "Unhealthy"
        return f"{self.service_name} - {status}"
