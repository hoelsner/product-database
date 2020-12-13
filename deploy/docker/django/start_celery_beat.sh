#!/usr/bin/env bash
echo "wait for database to be active..."
while !</dev/tcp/database/5432; do sleep 1; done;
echo "wait for redis to be active..."
while !</dev/tcp/redis/6379; do sleep 1; done;

echo "start celery beat..."
cd /var/www/productdb/source
celery -A django_project beat \
        --loglevel=${DJANGO_LOG_LEVEL}
