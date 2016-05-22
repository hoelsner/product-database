from celery.schedules import crontab

from django_project.settings.common import *

#
# Celery configuration
#
import djcelery
INSTALLED_APPS = INSTALLED_APPS + ('djcelery',)

BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# task results expire after 4 weeks
CELERY_TASK_RESULT_EXPIRES = 2419200
CELERYBEAT_SCHEDULE_FILENAME = "../celerybeat-schedule.db"
CELERYBEAT_PIDFILE = "../celerybeat.pid"
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_TIMEZONE = TIME_ZONE
CELERYBEAT_SCHEDULE = {
    'periodic-sync-with-cisco-eox-api': {
        'task': 'ciscoeox.synchronize_with_cisco_eox_api',
        'schedule': crontab(hour=3, minute=0, day_of_week=5)
    },
}


djcelery.setup_loader()
