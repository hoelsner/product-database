#!/usr/bin/env bash
echo "wait for database to be active..."
while !</dev/tcp/database/5432; do sleep 1; done;
echo "wait for redis to be active..."
while !</dev/tcp/redis/6379; do sleep 1; done;

gunicorn django_project.wsgi:application --bind 0.0.0.0:8443 --env DJANGO_SETTINGS_MODULE=django_project.settings \
    --workers ${PDB_GUNICORN_WORKER} \
    --log-level=${DJANGO_LOG_LEVEL} \
    --limit-request-line 6144 \
    --keep-alive 300 \
    --ssl-version 2 \
    --capture-output \
    --access-logfile - \
    --error-logfile - \
    --certfile /var/www/productdb/ssl/gunicorn.crt \
    --keyfile /var/www/productdb/ssl/gunicorn.key \
