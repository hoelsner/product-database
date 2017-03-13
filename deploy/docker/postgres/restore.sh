#!/usr/bin/env bash
export PGPASSWORD=$POSTGRES_PASSWORD

if [ -z "$1" ]
then
    echo "use restore.sh <filename-in-backup-directory>"
else
    echo "restore database file $1..."
    dropdb -h database -U $POSTGRES_USER $POSTGRES_DB
    createdb -h database -U $POSTGRES_USER $POSTGRES_DB
    psql -h database -U $POSTGRES_USER $POSTGRES_DB < /backups/$1
fi
