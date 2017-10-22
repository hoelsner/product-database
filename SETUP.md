# Setup & Installation

## Stage a Demo Instance (for testing only)

You can download the Docker Community Edition for free on the [Docker Homepage](https://www.docker.com/get-docker).
 After a successful Docker installation, use the following commands to create a new demo instance of the Product Database:

```bash
git clone https://github.com/hoelsner/product-database.git
docker build -f deploy/docker/Dockerfile-basebox -t productdb/basebox:latest .
docker-compose -p productdb build
docker-compose -p productdb up -d database redis
docker-compose -p productdb up build_deps
docker-compose -p productdb up -d
```

**Please note:** The docker-compose file will expose port 80 and 443 on your Machine for the Product Database by default. If
 you have a local webserver already running, set the `NGINX_HTTP_PORT` and `NGINX_HTTPS_PORT` environment variable. Otherwise
 the `docker-compose -p productdb up -d` command will fail.

After a successful execution of the commands, the Product Database is available at https://localhost. The default admin username/password is `pdb_admin/pdb_admin`.

To shutdown the demo instance, use the following command:

```
docker-compose -p productdb down -v
```

## Stage a Production Instance

The deployment of the Product Database is using docker-compose and includes all required components to get the service up an running (including the redis cache and the database).

### Server requirements

* 4 vCPU's
* min. 4 GB RAM
* Docker Engine (tested with Version 17.09.0-ce)
* Docker compose (tested with Version 1.16.1)

The Product Database is currently only tested in a Single Node Container Deployment.

### Single Node Container Deployment

After cloning the Product Database from GitHub copy the `env.prod_template` to `env.production`. Then update the configuration by replacing all `plschgme` values. There are also
 several optional configuration options available e.g. the LDAP authentication or the integration to a sentry logging system.  Please make a backup of this file, because you need
 it every time you work on the instance.

The following table shows all configuration options that are available in the system:

^ environment variable   ^ description                 ^ default value  ^
|------------------------|-----------------------------|----------------|
| DJANGO_SECRET_KEY      | Django secret key           | plschgme       |
| DJANGO_LOG_LEVEL       | Django log level            | info           |
| PDB_DATABASE_NAME      | Database name               | postgres       |
| PDB_DATABASE_USER      | Database user               | postgres       |
| PDB_DATABASE_PASSWORD  | Database password           | <not set>      |
| PDB_DATABASE_HOST      | Database host               | 127.0.0.1      |
| PDB_DATABASE_PORT      | Database port               | 5432           |
| PDB_REDIS_HOST         | redis-server host           | localhost      |
| PDB_REDIS_PORT         | redis-server port           | 6379           |
| PDB_GUNICORN_WORKER    | worker processes per web container    | 3           |
| PDB_CELERY_CONCURRENCY | worker processes per celery worker    | 4           |
| PDB_LANGUAGE_CODE      | language code for django           | en-us          |
| PDB_TIME_ZONE          | time zone in django config         | Europe/Berlin  |
| PDB_TIME_FORMAT        | time format in django config       | P              |
| PDB_DATE_FORMAT        | date format in django config       | N j, Y         |
| PDB_SHORT_DATE_FORMAT  | short date format in django config | Y-m-d          |
| PDB_ENABLE_SENTRY      | enable sentry logging              | <not set>     |
| PDB_SENTRY_DSN         | sentry DSN                         | <not set>     |
| PDB_LDAP_ENABLE         | enable LDAP authentication         | <not set>                           |
| PDB_LDAP_SERVER_URL     | LDAP Server URL                    | ldap://127.0.0.1:389/               |
| PDB_LDAP_BIND_DN        | LDAP server user                   | cn=django-agent,dc=example,dc=com   |
| PDB_LDAP_BIND_PASSWORD  | LDAP server passowrd               |                                     |
| PDB_LDAP_USER_SEARCH    | where to search for the user       | ou=users,dc=example,dc=com          |
| PDB_LDAP_GROUP_SEARCH   | where to search for the groups     |                                     |
| PDB_LDAP_REQUIRE_GROUP  | group of the user that is required |                                     |
| PDB_DEBUG              | enable debug mode                  | <not set>     |
| PDB_TESTING            | used when running the test cases   | <not set>     |
| PDB_DEBUG_CACHE        | enable redis cache in debug mode   | <not set>     |
| PDB_DISABLE_CACHE      | disable cacheops database caching  | <not set>     |
| HTTPS_SELF_SIGNED_CERT_COUNTRY        |          |               |
| HTTPS_SELF_SIGNED_CERT_FQDN           | Full Qualified Hostname         |               |

Now use the following commands to start the Product Database:

```
export INSTANCE_CONFIG=production
export COMPOSE_PROJECT_NAME=productdbprod

docker build -f deploy/docker/Dockerfile-basebox -t productdb/basebox:latest .
docker-compose -p productdb build

docker-compose up -d database redis
docker-compose up build_deps
docker-compose up -d
```

By default the Product Database will run on Port 80 (HTTP) and Port 443 (HTTPs). The default admin username/password is `pdb_admin/pdb_admin`.

If you have a local webserver already running, set the `NGINX_HTTP_PORT` and `NGINX_HTTPS_PORT` environment variable. Otherwise
 the `docker-compose -p productdb up -d` command will fail.

### Backup & Restore

The database container provides several scripts for backup/restore purpose. These backup are stored in the named volume `postgres_backup`.
 You can use one of the following commands to take a backup, view a list with all backups and restore the database from a file. Please note that
 the restore operation require a shutdown of all services except the database.

```bash
export INSTANCE_CONFIG=production
export COMPOSE_PROJECT_NAME=productdbprod

docker-compose exec database backup
docker-compose exec database list-backups
docker-compose exec database restore <filename>
```

### Update an existing instance

To update an existing instance, you need to rebuild the containers:

```bash
export INSTANCE_CONFIG=production
export COMPOSE_PROJECT_NAME=productdbprod

docker-compose down
git pull origin master
docker-compose up -d --build --force-recreate
```
