#!/usr/bin/env bash

#
# configure_maintenance_script.sh <sitename> <user-id> <group-id> <deployment-type>
#

# cleanup
file=/bin/configure_$1
if [ -f "$file" ]
then
    sudo rm ${file}
fi

# create final_configuration script
# script is executed in {{ site_directory }}/{{ site_name }}/source/

SOURCE_DIR=$(pwd)
SOURCE_DIR=$(echo ${SOURCE_DIR} | sed 's_/_\\/_g')
echo ${SOURCE_DIR}

sed "s/SITENAME/$1/g" build-scripts/appliance/template/maintenance/configure_sitename.sh | sudo tee /bin/configure_$1
sed "s/SOURCE_DIR/$SOURCE_DIR/g" /bin/configure_$1 | sudo tee /bin/configure_$1
sed "s/USER_ID/$2/g" /bin/configure_$1 | sudo tee /bin/configure_$1
sed "s/GROUP_ID/$3/g" /bin/configure_$1 | sudo tee /bin/configure_$1

chmod 775 /bin/configure_$1
chown $2 /bin/configure_$1
chgrp $3 /bin/configure_$1

# configure restart-local-services.yaml
sed "s/SITENAME/$1/g" build-scripts/appliance/template/maintenance/restart_sitename.sh | sudo tee /bin/restart_$1
sed "s/USER_ID/$2/g" /bin/restart_$1 | sudo tee /bin/restart_$1

sed "s/var_sitename/$1/g" build-scripts/appliance/template/maintenance/restart-local-services.yaml | sudo tee /etc/ansible/$1-restart-local-services.yaml
sed "s/var_deployment-type/$4/g" /etc/ansible/$1-restart-local-services.yaml | sudo tee /etc/ansible/$1-restart-local-services.yaml
sed "s/USER_ID/$2/g" /etc/ansible/$1-restart-local-services.yaml | sudo tee /etc/ansible/$1-restart-local-services.yaml

chmod 775 /bin/restart_$1
chown $2 /bin/restart_$1
chgrp $3 /bin/restart_$1

chown $2 /etc/ansible/$1-restart-local-services.yaml
chgrp $3 /etc/ansible/$1-restart-local-services.yaml