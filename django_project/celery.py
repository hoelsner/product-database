from __future__ import absolute_import

import logging
import os
from celery import Celery, states
from django.conf import settings
from django.core.cache import cache

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
app = Celery('product_db')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


class TaskState(object):
    """
    states used for celery tasks
    """
    SUCCESS = states.SUCCESS
    FAILED = states.FAILURE
    STARTED = states.STARTED
    PROCESSING = "processing"
    PENDING = states.PENDING


def get_meta_data_for_task(task_id):
    try:
        meta_data = cache.get("task_meta_%s" % task_id, {})

    except Exception:  # catch any exception
        logging.debug("no meta information for task '%s' found" % task_id, exc_info=True)
        meta_data = {}
    return meta_data


def set_meta_data_for_task(task_id, title, redirect_to=None, auto_redirect=True):
    meta_data = {
        "title": title,
        "auto_redirect": auto_redirect
    }
    if redirect_to:
        meta_data["redirect_to"] = redirect_to

    cache.set("task_meta_%s" % task_id, meta_data, 60 * 60 * 8)
