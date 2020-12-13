#!/usr/bin/env bash
##################################################################################
#
# bootstrap script to get the Product Database working
#
##################################################################################
set -e

file="/var/www/productdb/ssl/server.key"
if [ ! -f "$file" ]
then
    echo ""
    echo "==> SSL certificate not found, generate self-signed certificate..."
    echo ""
    openssl req -new -nodes -x509 -subj "/C=$HTTPS_SELF_SIGNED_CERT_COUNTRY/CN=$HTTPS_SELF_SIGNED_CERT_FQDN" -days 3650 -keyout /var/www/productdb/ssl/server.key -out /var/www/productdb/ssl/server.crt -extensions v3_ca
fi

file="/var/www/productdb/ssl/database.key"
if [ ! -f "$file" ]
then
    echo ""
    echo "==> Database certificate not found, generate self-signed certificate..."
    echo ""
    openssl req -new -nodes -x509 -subj "/C=$HTTPS_SELF_SIGNED_CERT_COUNTRY/CN=$HTTPS_SELF_SIGNED_CERT_FQDN" -days 3650 -keyout /var/www/productdb/ssl/database.key -out /var/www/productdb/ssl/database.crt -extensions v3_ca
    chmod 600 /var/www/productdb/ssl/database.key
    chgrp 999 /var/www/productdb/ssl/database.key
    chgrp 999 /var/www/productdb/ssl/database.crt
    chown 999 /var/www/productdb/ssl/database.key
    chown 999 /var/www/productdb/ssl/database.crt
fi

file="/var/www/productdb/ssl/gunicorn.key"
if [ ! -f "$file" ]
then
    echo ""
    echo "==> gunicorn certificate not found, generate self-signed certificate..."
    echo ""
    openssl req -new -nodes -x509 -subj "/C=$HTTPS_SELF_SIGNED_CERT_COUNTRY/CN=$HTTPS_SELF_SIGNED_CERT_FQDN" -days 3650 -keyout /var/www/productdb/ssl/gunicorn.key -out /var/www/productdb/ssl/gunicorn.crt -extensions v3_ca
fi

echo "wait for database to be active..."
while !</dev/tcp/database/5432; do sleep 1; done;
echo "wait for redis to be active..."
while !</dev/tcp/redis/6379; do sleep 1; done;

cd /var/www/productdb/source

echo ""
echo "==> apply database migrations and apply default data..."
echo ""

python3 manage.py migrate

flag_file="/var/www/productdb/data/provisioning"
if [ ! -f "$flag_file" ] || [ "$REBUILD_DB" == "1" ]
then
    echo ""
    echo "==> create database defaults..."
    echo ""
    python3 manage.py createcachetable
    python3 manage.py loaddata initial_data
    touch $flag_file

    if [ "$LOAD_SELENIUM_TEST_DATA" == "1" ]
    then
        echo ""
        echo "==> load test data for the selenium test cases"
        echo ""
        python3 manage.py loaddata selenium_tests
    fi
else
    echo ""
    echo "==> don't create database defaults"
    echo ""
fi

#echo ""
#echo "==> copy static data..."
#echo ""
#cp -Rf /var/www/productdb-static/lib /var/www/productdb/static

echo ""
echo "==> collect static files..."
echo ""
python3 manage.py collectstatic --noinput
