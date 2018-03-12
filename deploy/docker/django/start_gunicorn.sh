#!/usr/bin/env bash

gunicorn django_project.wsgi:application --bind 0.0.0.0:8000 \
        --workers ${PDB_GUNICORN_WORKER} \
        --log-level=${DJANGO_LOG_LEVEL} \
        --limit-request-line 6144 \
        --timeout 600 \
        --access-logfile=- \
        --error-logfile=- \
        --enable-stdio-inheritance
