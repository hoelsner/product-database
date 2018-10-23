#!/usr/bin/env bash
export PGPASSWORD=$POSTGRES_PASSWORD

if [ -z "$1" ]
then
    echo "use restore.sh <filename-in-backup-directory>"
else
    echo "restore database file $1 to database $POSTGRES_DB..."
    dropdb -h localhost -U $POSTGRES_USER $POSTGRES_DB
    pg_restore -h localhost -U $POSTGRES_USER -C -d postgres /backups/$1
fi
