FROM nginx:stable

RUN apt-get update \
    && apt-get install -y \
        python3 \
        python3-pip \
    && pip3 install docker-py

ENV PDB_GUNICORN_WORKER 3

ADD ./deploy/docker/nginx /etc/nginx/template

EXPOSE 443
EXPOSE 80

CMD python3 /etc/nginx/template/update_nginx_config.py && nginx -g "daemon off;"
