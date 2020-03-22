from celery.schedules import crontab
from django_project.settings.common import *

#
# Celery configuration
#
#redis_server = os.environ.get("PDB_REDIS_HOST", "127.0.0.1")
#redis_port = os.environ.get("PDB_REDIS_PORT", "6379")

BROKER_URL = "redis://:%s@%s:%s" % (os.environ.get("PDB_REDIS_PASSWORD", ""), redis_server, redis_port)
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = os.getenv("PDB_TIME_ZONE", "Europe/Berlin")
CELERY_RESULT_BACKEND = "django-db"  # "redis://:%s@%s:%s" % (os.environ.get("PDB_REDIS_PASSWORD", ""), redis_server, redis_port)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TRACK_STARTED = True
CELERY_RESULT_PERSISTENT = True
CELERY_TASK_RESULT_EXPIRES = 2419200
CELERYBEAT_SCHEDULE_FILENAME = "../data/celerybeat-schedule.db"
CELERYBEAT_PIDFILE = "../celerybeat.pid"
CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERYD_PREFETCH_MULTIPLIER = os.environ.get("PDB_CELERY_CONCURRENCY", 4)
CELERYBEAT_SCHEDULE = {
    "periodic-sync-with-cisco-eox-api": {
        "task": "ciscoeox.synchronize_with_cisco_eox_api",
        "schedule": crontab(hour=2, minute=0, day_of_week=5)
    },
    # set the lc_state_sync flag on Cisco equipment based on the configuration values
    "ciscoeox.populate_product_lc_state_sync_field": {
        "task": "ciscoeox.populate_product_lc_state_sync_field",
        "schedule": crontab(hour=1, minute=0)
    },
    # remove all product checks every Sunday at midnight
    "productdb.delete_all_product_checks": {
        "task": "productdb.delete_all_product_checks",
        "schedule": crontab(hour=0, minute=0, day_of_week=0)
    }
}
