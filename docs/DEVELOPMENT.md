# Development Notes

## Setup a local development environment

To start all required services on the local computer use the `docker-compose_dev.yaml` file (can also be used as a remote interpreter in several IDE's). 

```
docker-compose -f docker-compose_dev.yaml up -d
```

## Django development server

There are two steps required before starting the development server: collect the static dependencies (CSS, JS etc.) and create the database with the initial data.

The static files can be downloaded using npm:

```
npm install
./node_modules/grunt-cli/bin/grunt copy
./node_modules/grunt-cli/bin/grunt clean
```

To create the database and load the initial data, use the following commands:

```
export PDB_DEBUG=1 
python3 manage.py collectstatic
python3 manage.py migrate
python3 manage.py loaddata default_users default_vendors initial_data
```

The Django development server can be started with the command `python3 manage.py runserver`

## run the unit test cases

The following environment parameters and commands are required to start the unit-tests:

```
export PDB_TESTING=1
export TEST_CISCO_API_CLIENT_ID=client_id
export TEST_CISCO_API_CLIENT_SECRET=client_secret

# if you use a local postgres and redis server, you need to update the following configuration variables
export PDB_DATABASE_HOST=localhost
export PDB_REDIS_HOST=localhost

pytest
```

The following custom parameters are used to run tests with external dependencies:

 * `--online` - include Cisco EoX API unit-tests (internet connections and `.cisco_api_credentials` required)
 * `--selenium` - run selenium test cases (a local instance of the Product Database is started)

## run the selenium test cases (on Firefox)

Before using the `--selenium` flag with py.test, a local test instance of the Product Database is created and started within pytest:

```
docker-compose -p productdbtesting -f docker-compose_test.yaml build --pull
docker-compose -p productdbtesting -f docker-compose_test.yaml up -d
docker-compose -p productdbtesting -f docker-compose_test.yaml down -v
```

A valid geckodriver must be installed and available at `/usr/local/bin/geckodriver`. This path can be overwritten with the parameter `FIREFOX_DRIVER_EXEC_PATH`.
