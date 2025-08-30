import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

app = Celery("crm")

# Load config from settings.py with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks.py in all installed apps
app.autodiscover_tasks()
