#!/usr/bin/env bash
echo "wait for database to be active..."
while !</dev/tcp/database/5432; do sleep 1; done;
echo "wait for redis to be active..."
while !</dev/tcp/redis/6379; do sleep 1; done;

echo "start celery worker..."
cd /var/www/productdb/source
celery -A django_project worker \
        --concurrency=${PDB_CELERY_CONCURRENCY} \
        --loglevel=${DJANGO_LOG_LEVEL} \
        --events \
        --time-limit=14400 \
        --soft-time-limit=10800 \
        --statedb=/var/www/productdb/data/celerybeat-schedule.db
