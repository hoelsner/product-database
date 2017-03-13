from __future__ import absolute_import

import logging
import os
import celery
import raven
from celery import states
from django.conf import settings
from django.core.cache import cache
from raven.contrib.celery import register_signal, register_logger_signal


class Celery(celery.Celery):

    def on_configure(self):
        if settings.PDB_ENABLE_SENTRY: # ignore for coverage
            client = raven.Client(settings.PDB_SENTRY_DSN)
            client.release = raven.fetch_git_sha(os.path.dirname(os.pardir))

            # register a custom filter to filter out duplicate logs
            register_logger_signal(client)

            # hook into the Celery error handler
            register_signal(client)


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


def is_worker_active():
    try:
        i = app.control.inspect()
        if i.registered():
            return True

    except:
        pass

    logging.error("Celery Worker process not available")
    return False


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


@app.task
def hello_task():
    logging.info("Hello Task called")
    return {
        "hello": "task"
    }
