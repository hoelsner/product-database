FROM ubuntu:18.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONIOENCODING utf-8
ENV DJANGO_SECRET_KEY PlsChgMe
ENV DJANGO_LOG_LEVEL info
ENV POSTGRES_DB productdb
ENV POSTGRES_USER postgres
ENV POSTGRES_PASSWORD plschgme
ENV PDB_DATABASE_HOST database
ENV PDB_DATABASE_PORT 5432
ENV PDB_REDIS_HOST redis
ENV PDB_REDIS_PORT 6379

# gunicorn variables
ENV PDB_GUNICORN_WORKER 2

# celery worker variables
ENV PDB_CELERY_CONCURRENCY 2

RUN echo \
    && apt-get update  \
    && apt-get install -y \
        python3.5 \
        python3-pip \
        python3-dev \
        python-psycopg2 \
        libpq-dev \
        libsasl2-dev \
        libldap2-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

ADD . /var/www/productdb/source
RUN echo \
    && pip3 install --no-cache-dir -r /var/www/productdb/source/requirements.txt \
    && mkdir /var/www/productdb/logs

WORKDIR /var/www/productdb/source

EXPOSE 8000

ADD ./deploy/docker/django/start_gunicorn.sh /usr/local/bin/start_gunicorn
ADD ./deploy/docker/django/start_celery_camera.sh /usr/local/bin/start_celery_camera
ADD ./deploy/docker/django/start_celery_worker.sh /usr/local/bin/start_celery_worker
ADD ./deploy/docker/django/start_celery_beat.sh /usr/local/bin/start_celery_beat
ADD ./deploy/docker/django/initialimport.sh /usr/local/bin/initialimport
ADD ./deploy/docker/django/initialimportstatus.sh /usr/local/bin/initialimportstatus

CMD ["start_gunicorn"]