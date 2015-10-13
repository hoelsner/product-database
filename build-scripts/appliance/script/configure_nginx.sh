#!/usr/bin/env bash
# configure_environment.sh <sitename>
#
# cleanup if the site already exist
sudo rm /etc/nginx/sites-available/$1
sudo rm /etc/nginx/sites-enabled/$1

SITE_DIR=$(pwd)
SITE_DIR=$(echo ${SITE_DIR} | sed 's_/_\\/_g')
echo ${SITE_DIR}

# build configs from templates
# script is executed in {{ site_directory }}/{{ site_name }}/
cd source
sed "s/SITENAME/$1/g" build-scripts/appliance/template/nginx.template.conf | sudo tee /etc/nginx/sites-available/$1
sed "s/SITE_DIR/${SITE_DIR}/g" /etc/nginx/sites-available/$1 | sudo tee /etc/nginx/sites-available/$1

# configure nginx
cd /etc/nginx/
sudo ln -s /etc/nginx/sites-available/$1 /etc/nginx/sites-enabled/$1
