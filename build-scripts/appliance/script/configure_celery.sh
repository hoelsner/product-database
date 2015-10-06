#!/usr/bin/env bash
# configure_celery.sh <sitename> <user-id> <group-id>
#
# cleanup if files are already exist
file=/etc/init/celeryworker-$1.conf
if [ -f "$file" ]
then
    sudo rm ${file}
fi

file=/etc/init/celerycam-$1.conf
if [ -f "$file" ]
then
    sudo rm ${file}
fi


# build configs from templates
# script is executed in {{ site_directory }}/{{ site_name }}/source/
sed "s/SITENAME/$1/g" build-scripts/appliance/template/celeryworker-upstart.template.conf | sudo tee /etc/init/celeryworker-$1.conf
sed "s/USER_ID/$2/g" /etc/init/celeryworker-$1.conf | sudo tee /etc/init/celeryworker-$1.conf
sed "s/GROUP_ID/$3/g" /etc/init/celeryworker-$1.conf | sudo tee /etc/init/celeryworker-$1.conf

sed "s/SITENAME/$1/g" build-scripts/appliance/template/celerycam-upstart.template.conf | sudo tee /etc/init/celerycam-$1.conf
sed "s/USER_ID/$2/g" /etc/init/celerycam-$1.conf | sudo tee /etc/init/celerycam-$1.conf
sed "s/GROUP_ID/$3/g" /etc/init/celerycam-$1.conf | sudo tee /etc/init/celerycam-$1.conf
