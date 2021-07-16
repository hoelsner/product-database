# Setup & Installation

## Create a Demo Instance (for testing only)

You can download the Docker Community Edition for free on the [Docker Homepage](https://www.docker.com/get-docker).
 After the successful Docker installation, use the following commands to create a new demo instance of the Product Database:

```bash
git clone --branch stable https://github.com/hoelsner/product-database.git
docker-compose -p productdb -f docker-compose.template.yaml build --pull
docker-compose -p productdb -f docker-compose.template.yaml up -d
```

**Please note:** The docker-compose file will expose ports 80 and 443 on your machine for the Product Database by default. If a local webserver is already running this command will fail. In this case, you need to set the `NGINX_HTTP_PORT` and `NGINX_HTTPS_PORT` environment variables. Otherwise, the `docker-compose -p productdb up -d` command will fail.

The Product Database is available at `https://localhost` after successful execution of the command. The default admin username and password is `pdb_admin`. To shutdown the demo instance and remove all data, use the following command:

```bash
docker-compose -p productdb down -v
```

## Create a Production Instance

You need a Linux server running docker and docker-compose with at least the following hardware requirements:

* 4 vCPU's
* min. 4 GB RAM

After you clone the repository to the server, you need to build the containers and copy the `docker-compose.template.yaml` file to `docker-compose.yaml` for configuration:

```bash
git clone --branch stable https://github.com/hoelsner/product-database.git
docker-compose build --pull
cp docker-compose.template.yaml docker-compose.yaml
```

The docker-compose file is excluded from the git repository and you can therefore maintain the configuration options locally. Now you just need to update the configuration value by replacing (at least) all `plschgme` values. There are also several optional configuration options available e.g. the LDAP authentication or the integration to a Sentry logging system.

The following table shows all configuration options that are available for the application:

| environment variable   | description                 | default value  |
| ---------------------- | --------------------------- | -------------- |
| `DJANGO_SECRET_KEY`      | Django secret key           | plschgme       |
| `DJANGO_LOG_LEVEL`       | Django log level            | info           |
| `PDB_DATABASE_NAME`      | Database name               | postgres       |
| `PDB_DATABASE_USER`      | Database user               | postgres       |
| `PDB_DATABASE_PASSWORD`  | Database password           | <not set>      |
| `PDB_DATABASE_HOST`      | Database host               | 127.0.0.1      |
| `PDB_DATABASE_PORT`      | Database port               | 5432           |
| `PDB_REDIS_HOST`         | redis-server host           | localhost      |
| `PDB_REDIS_PORT`         | redis-server port           | 6379           |
| `PDB_GUNICORN_WORKER`    | worker processes per web container    | 3           |
| `PDB_CELERY_CONCURRENCY` | worker processes per celery worker    | 4           |
| `PDB_LANGUAGE_CODE`      | language code for django           | en-us          |
| `PDB_TIME_ZONE`          | time zone in django config         | Europe/Berlin  |
| `PDB_TIME_FORMAT`        | time format in django config       | P              |
| `PDB_DATE_FORMAT`        | date format in django config       | N j, Y         |
| `PDB_SHORT_DATE_FORMAT`  | short date format in django config | Y-m-d          |
| `PDB_ENABLE_SENTRY`      | enable sentry logging              | <not set>     |
| `PDB_SENTRY_DSN`         | sentry DSN                         | <not set>     |
| `PDB_LDAP_ENABLE`         | enable LDAP authentication         | <not set>                           |
| `PDB_LDAP_SERVER_URL`     | LDAP Server URL                    | ldap://127.0.0.1:389/               |
| `PDB_LDAP_BIND_DN`        | LDAP server user                   | cn=django-agent,dc=example,dc=com   |
| `PDB_LDAP_BIND_PASSWORD`  | LDAP server passowrd               |                                     |
| `PDB_LDAP_USER_SEARCH`    | where to search for the user       | ou=users,dc=example,dc=com          |
| `PDB_LDAP_GROUP_SEARCH`   | where to search for the groups     |                                     |
| `PDB_LDAP_REQUIRE_GROUP`  | group of the user that is required |                                     |
| `PDB_DEBUG`              | enable debug mode                  | <not set>     |
| `PDB_TESTING`            | used when running the test cases   | <not set>     |
| `PDB_DEBUG_CACHE`        | enable redis cache in debug mode   | <not set>     |
| `PDB_DISABLE_CACHE`      | disable cacheops database caching  | <not set>     |
| `HTTPS_SELF_SIGNED_CERT_COUNTRY`        |          |               |
| `HTTPS_SELF_SIGNED_CERT_FQDN`           | Full Qualified Hostname         |               |

Now use the following command to start the Product Database:

```bash
docker-compose up -d --scale web=2
```

By default, the Product Database will run on Port 80 (HTTP) and Port 443 (HTTPs). The default admin username/password is `pdb_admin/pdb_admin`. You can access the settings page using the top-left navigation at "Admin" > "Settings" (e.g. to configure the Cisco EoX API).

If a local webserver is already running, set the `NGINX_HTTP_PORT` and `NGINX_HTTPS_PORT` environment variables. Otherwise, docker-compose command will fail.

### Backup & Restore

You can perform a backup using the regular postgres commands (see https://www.postgresql.org/docs/12/backup.html) within the database container. The following commands can be used within the build-deps container (`/backups` is persisted in a volume by default): 

```bash
# go into the container
docker exec -it $(docker ps -q --filter label=productdb=build_deps) /bin/bash

# e.g. for Backup
export date=$(date '+%Y%m%d')
pg_dump -Fc -h database -U $POSTGRES_USER $POSTGRES_DB > /backups/$date-productdb_backup.pg_dump

# e.g. for Restore
dropdb -h localhost -U $POSTGRES_USER $POSTGRES_DB
pg_restore -h localhost -U $POSTGRES_USER -C -d postgres /backups/$1
```

### Update an existing instance

To update an existing instance (including postgres and redis), you need to update the git repository and rebuild the containers:

```bash
git pull origin stable 
git checkout stable
docker-compose build --pull
docker-compose up -d --force-recreate
```

### initial data import from Cisco EoX API

To fetch all data initially from the Cisco EoX API (one time import), you can use the following management command within the `web` container:

Before starting the import you need to configure the Cisco EoX API in the UI (Login as `pdb_admin` and enable the Cisco API with the credentials). The `initialimport` command requires a list of years that should be imported (e.g. `2017 2018` to import all Cisco EoX records that are announced in 2017 and 2018). Use the command `initialimportstatus` to verify the download-process.

```bash
docker exec -it $(docker ps -q --filter label=productdb=build_deps) /bin/bash

initialimport <years>
# e.g.
initialimport 2020 2019 2018

# verify the state of the import
initialimportstatus

# message if the initial import is still running
#   State:   processing
#   Message: fetch all information for year 2021...

# message if the process finished successfully
#   State:   SUCCESS
#   Message: The EoX data were successfully downloaded for the following years: 2021
```
