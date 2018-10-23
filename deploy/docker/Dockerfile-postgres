FROM postgres:9.6-alpine

ADD ./deploy/docker/postgres/backup.sh /usr/local/bin/backup
ADD ./deploy/docker/postgres/restore.sh /usr/local/bin/restore
ADD ./deploy/docker/postgres/list-backups.sh /usr/local/bin/list-backups

RUN chmod +x /usr/local/bin/restore
RUN chmod +x /usr/local/bin/backup
RUN chmod +x /usr/local/bin/list-backups
