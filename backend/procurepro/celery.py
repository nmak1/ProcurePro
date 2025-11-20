import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procurepro.settings')

app = Celery('procurepro')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи во всех приложениях
app.autodiscover_tasks(['apps.core', 'apps.orders', 'apps.products'])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')