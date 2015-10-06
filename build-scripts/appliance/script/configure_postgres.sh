#!/usr/bin/env bash
# configure_postgres.sh <sitename> <dbname> <user-id> <group-id>
#
secret_key="$(<'../secret_key.key')"
#
# passsword is set to the secret key of the page (is created at this stage of the script), this script is just called
# on the initial provisioning
#
# script is executed in {{ site_directory }}/{{ site_name }}/source/
sed "s/dbname/$2/g" build-scripts/appliance/template/postgres_create_user.sql | sudo tee ../database/postgres_create_user.sql
sed "s/var_username/$3/g" ../database/postgres_create_user.sql | sudo tee ../database/postgres_create_user.sql
sed "s/secret_key/$secret_key/g" ../database/postgres_create_user.sql | sudo tee ../database/postgres_create_user.sql

SOURCE_DIR=$(pwd)
echo ${SOURCE_DIR}

sudo -u postgres psql -f ${SOURCE_DIR}/../database/postgres_create_user.sql
sudo -u postgres createdb --owner $3 $2_database
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $2_database TO $3;"