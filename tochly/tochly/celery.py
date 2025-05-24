import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tochly.settings')

app = Celery('tochly')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
