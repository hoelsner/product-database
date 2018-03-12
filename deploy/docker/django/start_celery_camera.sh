#!/usr/bin/env bash

echo "start celery camera..."
cd /var/www/productdb/source
python3 manage.py celerycam --loglevel=${DJANGO_LOG_LEVEL}