"""Celery configuration for Smile Memory project."""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("smile_memory")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
