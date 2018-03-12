#!/usr/bin/env bash
##################################################################################
#
# Setup all external dependencies (Javascript and CSS)
#
##################################################################################
sleep 5
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
    python3 manage.py loaddata default_vendors default_text_blocks default_users
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

file="/var/www/productdb/ssl/server.key"
if [ ! -f "$file" ]
then
    echo ""
    echo "==> SSL certificate not found, generate self-signed HTTPs certificate..."
    echo ""
    openssl req -new -nodes -x509 -subj "/C=$HTTPS_SELF_SIGNED_CERT_COUNTRY/CN=$HTTPS_SELF_SIGNED_CERT_FQDN" -days 3650 -keyout /var/www/productdb/ssl/server.key -out /var/www/productdb/ssl/server.crt -extensions v3_ca
else
    echo ""
    echo "==> found SSL certificate, don't create a certificate"
    echo ""
fi

echo ""
echo "==> copy static data..."
echo ""
cp -Rf /var/www/productdb-static/lib /var/www/productdb/static

echo ""
echo "==> collect static files..."
echo ""
python3 manage.py collectstatic --noinput
