# Development Notes

This web service is based on python 3.5 and Django 1.11. A detailed list with all dependencies is available in the `requirements.txt` file.

## Setup a local development environment

Prior starting a local Django development server, a redis and postgres server must be reachable on localhost.
 The following commands will start these services as docker containers with the expected parameters.

```
docker container run -d --rm -p 127.0.0.1:5432:5432 -v productdb_dev_postgres:/var/lib/postgresql/data -e POSTGRES_DB=productdb --name dev_productdbpostgres postgres:9.6-alpine
docker container run -d --rm -p 127.0.0.1:6379:6379 -v productdb_dev_redis:/data --name dev_productdbredis redis:4.0-alpine
```

The Product Database uses python 3.5 and to run the development server, a virtual environment should be created.
 The python dependencies are saved in the `requirements.txt` and `requirements_dev.txt` files.

A separate json file at the root of the project is required to run the online unit-tests against the Cisco EoX API. The client credentials can be created at https://apiconsole.cisco.com.
 The JSON file `.cisco_api_credentials` must contain the following entries and is only locally saved (part of the gitignore):

```json
{
    "client_id": "",
    "client_secret": ""
}
```

## Django development server

There are two steps required before starting the development server: collect the static dependencies (CSS, JS etc.) and create the database with the initial data.

The static files can be downloaded using npm:

```
npm install
./node_modules/grunt-cli/bin/grunt copy
./node_modules/grunt-cli/bin/grunt clean
```

to create the database and load the initial data, use the following commands:

```
python3 manage.py collectstatic
python3 manage.py migrate
python3 manage.py loaddata default_users default_vendors default_text_blocks
```

The django development server can be started with the command `python3 manage.py runserver`

## run the unit test cases

The following commands will start all unit-tests (a flag to enable test mode is required):

```
export PDB_TESTING=1
py.test
```

The following custom parameters are used to run tests with external dependencies:

 * `--online` - include Cisco EoX API unit-tests (online, require the `.cisco_api_credentials` at the repository root)
 * `--selenium` - run selenium test cases (against a local instance of the Product Database, see below)

## run the selenium test cases (on Firefox)

Before using the `--selenium` flag with py.test, a local test instance of the Product Database must be created and started:

```
export COMPOSE_PROJECT_NAME=productdbtesting

docker-compose -p productdbtesting -f docker-compose_test.yaml build --pull
docker-compose -p productdbtesting -f docker-compose_test.yaml up -d database redis
docker-compose -p productdbtesting -f docker-compose_test.yaml up build_deps
docker-compose -p productdbtesting -f docker-compose_test.yaml up -d web worker beat nginx

docker-compose -p productdbtesting -f docker-compose_test.yaml down -v
```

A valid geckodriver must be installed and available at `/usr/local/bin/geckodriver`. This path can be overwritten with the parameter `FIREFOX_DRIVER_EXEC_PATH`.