#!/usr/bin/env bash

#
# configure_gunicorn.sh <sitename> <user-id> <group-id>
#

# cleanup
file=/etc/init/gunicorn-$1.conf
if [ -f "$file" ]
then
    sudo rm ${file}
fi

# build configs from templates
sed "s/SITENAME/$1/g" build-scripts/appliance/template/gunicorn-upstart.template.conf | sudo tee /etc/init/gunicorn-$1.conf
sed "s/USER_ID/$2/g" /etc/init/gunicorn-$1.conf | sudo tee /etc/init/gunicorn-$1.conf
sed "s/GROUP_ID/$3/g" /etc/init/gunicorn-$1.conf | sudo tee /etc/init/gunicorn-$1.conf
