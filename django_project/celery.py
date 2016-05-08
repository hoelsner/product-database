from __future__ import absolute_import
import os
import random

import time
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
app = Celery('product_db')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task
def add(x, y):
    """
    Simple debug function
    """
    delay = random.randint(1, 60)
    time.sleep(delay)
    return x + y
