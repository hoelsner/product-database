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

# build variables
ENV HTTPS_SELF_SIGNED_CERT_COUNTRY "Germany"
ENV HTTPS_SELF_SIGNED_CERT_FQDN "productdb"

RUN echo \
    && apt-get update  \
    && apt-get install -y \
        curl \
        build-essential \
        python3.5 \
        python3-pip \
        python3-dev \
        python-psycopg2 \
        libpq-dev \
        libsasl2-dev \
        libldap2-dev \
        libssl-dev \
        git \
    && curl -sL https://deb.nodesource.com/setup_8.x | bash - \
    && apt-get update  \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

ADD . /var/www/productdb/source
RUN echo \
    && pip3 install --no-cache-dir -r /var/www/productdb/source/requirements.txt \
    && mkdir /var/www/productdb/logs

WORKDIR /var/www/productdb/source

# install frontend deprendencies as part of the image (for later offline use)
RUN npm install \
    && /var/www/productdb/source/node_modules/.bin/grunt copy \
    && /var/www/productdb/source/node_modules/.bin/grunt clean

# copy static directory to container directory
RUN mkdir /var/www/productdb-static \
    && mkdir /var/www/productdb-static/lib \
    && cp -Rf /var/www/productdb/source/static/lib /var/www/productdb-static

## Clean up
RUN rm -rf /var/www/productdb/source/node_modules \
    && rm -rf /var/www/productdb/source/static/lib \
    && rm -rf /var/lib/apt/lists/*

RUN chmod +x ./deploy/docker/build_deps/build_dependencies.sh
CMD ./deploy/docker/build_deps/build_dependencies.sh
