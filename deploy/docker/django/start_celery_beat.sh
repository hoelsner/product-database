#!/usr/bin/env bash

echo "start celery beat..."
cd /var/www/productdb/source
celery beat -A django_project \
        --loglevel=${DJANGO_LOG_LEVEL}
