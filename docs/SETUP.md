# Setup & Installation

## Stage a Demo Instance (for testing only)

You can download the Docker Community Edition for free on the [Docker Homepage](https://www.docker.com/get-docker).
 After a successful Docker installation, use the following commands to create a new demo instance of the Product Database:

```bash
git clone https://github.com/hoelsner/product-database.git
docker-compose -p productdb -f docker-compose.template.yaml build
docker-compose -p productdb -f docker-compose.template.yaml up -d
```

**Please note:** The docker-compose file will expose port 80 and 443 on your Machine for the Product Database by default. If a local webserver is already running this command will fail. In this case, you need to set the `NGINX_HTTP_PORT` and `NGINX_HTTPS_PORT` environment variable. Otherwise the `docker-compose -p productdb up -d` command will fail.

The Product Database is available at `https://localhost` after successful execution of the command. The default admin username and password is `pdb_admin`. To shutdown the demo instance, use the following command:

```
docker-compose -p productdb down -v
```

## Stage a Production Instance

The deployment of the Product Database utilizes docker-compose which includes all required components to get the service up and running.

### Server requirements

* 4 vCPU's
* min. 4 GB RAM
* Docker Engine (tested with Version >=17.09.0-ce)
* Docker compose

The Product Database is currently only tested within a Single Node Container environment.

### Single Node Container Deployment

You need to clone the git repository to the server. Then you copy the `docker-compose.template.yaml` file to `docker-compose.yaml` with the following command:

```
cp docker-compose.template.yaml docker-compose.yaml --scale worker=2 web=2
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

```
docker-compose up -d
```

By default, the Product Database will run on Port 80 (HTTP) and Port 443 (HTTPs). The default admin username/password is `pdb_admin/pdb_admin`.

If a local webserver is already running, set the `NGINX_HTTP_PORT` and `NGINX_HTTPS_PORT` environment variable. Otherwise, docker-compose command will fail.

### Backup & Restore

The custom postgres container with the backup and restore scripts was replaced with the stock postgres container in this release. You must therefore use the commands described in the postgres documentation (at https://www.postgresql.org/docs/12/backup.html) to perform these operations. 

```bash
# e.g. for Backup
pg_dump -Fc -h database -U $POSTGRES_USER $POSTGRES_DB > /backups/$filename

# e.g. for Restore
dropdb -h localhost -U $POSTGRES_USER $POSTGRES_DB
pg_restore -h localhost -U $POSTGRES_USER -C -d postgres /backups/$1
```

### Update an existing instance

To update an existing instance, you need to rebuild the containers:

```bash
docker-compose down
git pull origin master
docker-compose up -d --build --force-recreate
```

### initial data import from Cisco EoX API

To fetch all data initially from the Cisco EoX API (one time import), you can now use the following management command within a `web` services container:

```
initialimport <years>
# e.g.
initialimport 2020 2019 2018
```

Before starting the import you need to configure the Cisco EoX API in the UI (Login as `pdb_admin` and enable the Cisco API with the credentials). The `initialimport` command requires a list of years that should be imported (e.g. `2017 2018` to import all Cisco EoX records that are announced in 2017 and 2018). Use the command `initialimportstatus` to verify the download-process. After the database update is finished, a notification is added to the homepage.
