#!/usr/bin/env bash
export PGPASSWORD=$POSTGRES_PASSWORD

filename=backup_$(date +'%Y_%m_%dT%H_%M_%S').dump

echo "create database backup file $filename"
pg_dump -Fc -h database -U $POSTGRES_USER $POSTGRES_DB > /backups/$filename
