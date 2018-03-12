#!/usr/bin/env bash

echo "start celery worker..."
cd /var/www/productdb/source
celery worker -A django_project \
        --concurrency=${PDB_CELERY_CONCURRENCY} \
        --loglevel=${DJANGO_LOG_LEVEL} \
        --events \
        --time-limit=14400 \
        --soft-time-limit=10800 \
        --statedb=/var/www/productdb/data/celerybeat-schedule.db
