
# Product Database

Version 0.2 - see [Changelog](CHANGELOG.md) for details

This Django based web service provides a central point of management for product information, which is targeted primarily for network products. The primary intention to create this the web service was to get in touch with the Django web framework and to create a tool, which automates end of life checks for various Cisco products.

It currently focuses to the following use cases:

* automatic check of lifecycle states for a list of products against the local database (bulk EoL check)
* REST API access to a central database which holds various information about products from network vendors
* import products using an Excel template (limited to 20000 records per Excel file)
* easy setup on a single Linux Server using Ansible

This web service is based on python 3.4.3 and Django 1.8. It uses the following packages and libraries:

* [Django Web Framework Version 1.8](https://www.djangoproject.com/)
* [Bootstrap 3.3](http://getbootstrap.com/)
* [Datatables.net (Version 1.10.8)](http://datatables.net/) with [Datatables buttons extension](https://datatables.net/extensions/buttons/)
* [Celery](http://www.celeryproject.org/)
* [Django REST framework](http://www.django-rest-framework.org)
* Django REST swagger
* django-celery
* django-datatables-view
* django-annoying
* gunicorn
* pandas
* xlrd
* requests
* redis
* [JSZip](https://stuk.github.io/jszip/) Version 2.5 (required for buttons extension)
* [PDFMake](http://pdfmake.org) Version 0.1.18 (required for buttons extension)
* selenium (for test only) 

## License

See the [license](LICENSE.md) file for license rights and limitations (MIT).

## Server requirements

* min. 1 GB RAM

## Cisco EoX API

This version is capable to synchronize with Cisco EoX API to crawl lifecycle data. It can be executed manually or runs as a background task to update the local database.

You can configure this crawler in two modes: 

* update the products that are created using the API
* update and create the products if necessary
  
For more information about the Cisco APIs see http://apiconsole.cisco.com for further details, Cisco Partner access only.

This web-service is able to interact with the Cisco API console (partner access only). Further details and descriptions of this API are outlined at http://apiconsole.cisco.com. Please note the Terms & Conditions of this Service (http://www.cisco.com/web/siteassets/legal/terms_condition.html).

### Activating the API Access
 
To use the Web-Service with the Cisco API console, you need to enter the client credentials on the settings page within the Web-Service. To run the test cases, please have a look at the development notes below.

These credentials can be created in the Cisco API administration. The following services are required:

* Hello API (to verify the API credentials)
* EoX API

## Setup and Installation

Please note that the build-scripts 

### using Vagrant (production)

This project is shipped with a vagrant file along with some Ansible playbooks. To run it out of the box using Vagrant just clone the repository and run

    $ vagrant up productdb
  
This will create a local machine running the production configuration of the product database.

### Server setup

You can also setup the web service on a server. Please note, that this Django application must be the only application that's running on the server. It is tested with Ubuntu Version 14.04. In the `build-tools` directory, you find a template to stage the web service on a machine (folder `stage_template`). It will execute an Ansible playbook on the given server IPs from the custom Ansible inventory file within the same directory.

## detailed explanation of the build script 

### variables

The following variables are used within the ansible provisioning scripts of this project:

    site_name             Name of the page (usually the DNS name of the server)
                          (defaults to "productdb")
    site_directory        Location on the disk of the machine 
                          (defaults to "/var/www")
    site_user             username which is used for the site/processes
    site_group            group which is used to the site/processes
    system_source         identifies, where the files are located (used for Vagrant), set to "file" will 
                          instruct the playbooks to copy files from a local directory 
                          (defaults to "git")
    site_source           repository or file path of the django project
                          (defaults to github repository)
    site_source_branch    (only used with git) identifies the branch to checkout during the git
                          (defaults to the latest stable version)
    dbname                Valid postgres DB name (alphanumeric with underscores)
                          (defaults to "productdatabase")
    deployment_type       Type of deployment, will enable debugging if set to development
                          (defaults to "production")
    ignore_allowedhosts   instructs the configuration script for the site to skip the creation of the 
                          ALLOWED_HOSTS variable within the deploy configuration (limit the access to the 
                          Django app to specific targets)

### directory structure

The following directory structure is used on the appliance.

    SITE_DIRECTORY
    |-> SITE_NAME
    |   |-> source          sourcecode of the page (the django project / git repository itself)
    |   |-> static          any static file (output of collect static files, served by nginx)
    |   |-> database        the database directory if using SQLite
    |   |-> virtualenv      the virtualenv for the page (used by gunicorn and celery) 
    |   |-> logs            log files of the page (except nginx)
    |   |-> secret_key.key  key for the page which is loaded in the Django configuration

### Used packages and libraries

Always installed packages:

* Python3
* python3 pip
* python virtualenv
* nginx
* ansible
* redis
* git
* postgresql
* postgresql contrib
* postgresql-server-dev-9.3

The required python libraries are outlined in the [requirements.txt](requirements.txt)

### Django configuration

When executing the Ansible playbook for provisioning, it will execute the python script located at `build-scripts/script/configure_site_settings.py` which creates a random security key located at the `SITE_SOURCE` directory and a `deploy.py` configuration in the `/django_project/settings` path on the server. This will be included in the server environment. 

Furthermore it will set the allowed hosts variable to the site name, if the `ignore_allowedhosts` is set to false during staging.

### appliance provisioning

This project ships with a Vagrantfile which creates a VM based on a public Ubuntu trusty64 base box and a set of Ansible playbooks for provisioning. There are two options available:

* Local copy of the source files (required for vagrant deployment)
* Git clone on the github repository (using the system_source parameter within the Ansible playbook)

Basically, you just need to write another YAML file for Ansible and include the `appliance-provision-tasks.yml` file from the `build-scripts` directory. As an alternative, you can copy the `stage_template` directory, which contains template files for staging (shell script to trigger the Ansible playbook, the Ansible playbook itself and an ansible-inventory, which defines the target server.

### default users

The staging script will create two users by default: one "admin" user with the password "admin", which can be used for administration tasks and one "api" user with the password "api" for write actions on the REST API. Any read action is permitted without authentication.

### maintenance scripts

The build tools integrate the following maintenance scripts:

    configure_<sitename>    initial configuration script (set the password for the admin user)
    restart_<sitename>      restart all services of the product database (su privileges required)

To create a backup of the relevant database content, you can use the following two python scripts:

* `app/create_backup.py` - create a backup of the relevant database objects and save the result to the `../backup` directory on the server
* `app/restore_backup.py` - restore a backup from the `../backup` directory on the server

## development notes

### executing the test cases

Before running the test cases, you need access to the Cisco API console. Copy the file `ciscoapi.client_credentials.json.sample` from the root directory, rename it to `ciscoapi.client_credentials.json.bak` and enter the test credentials.

To get the unit tests running, you need to add a fixture to the `app/productdb/fixtures` directory. Copy the `cisco_api_test_credentials.yaml.sample` and rename it to `cisco_api_test_credentails.yaml` and enter your test credentials. 

The unit-tests are located at

    app/productdb/tests
  
There are several sets for the execution:

    app/productdb/tests/all_tests.py      all unit tests from the project
    app/productdb/tests/online_tests.py   all unit tests, that run against the Cisco API console and require an internet 
                                          connection and test credentials
    app/productdb/tests/offline_tests.py  all tests that don't require a internet connection or test credentials
                                        
There are several functional tests using selenium defined in the following directory:
                                      
    tests/functional_tests
    
They are structured similar to the unit-tests. There is also the possibility to run these tests against a remote server using the following command-line parameter:

    --liveserver=<ip/dns name>:<port>

### Import test data to a development server

The repository contains some fictional test data, which are used within the functional and/or unit tests. They are created during the test instantiation using the REST API and the JSON files from the following directory:

    tests/data/create_cisco_test_data.json
    tests/data/create_juniper_test_data.json
    
You can manually trigger the import to the web service using the scripts from the /tests/api python scripts.

    api_clean_db.py              will drop all elements from the product database
    api_create_test_data.py      will add test data to the product database
    api_create_and_clean_db.py   will create the data and drop it after a key is pressed (combines the last two scripts)

The scripts require the URL of the target server as a parameter. The create scripts have an additional parameter "real" that will import the test data from the JSON files. If this argument is not set, the data is generated dynamically. 

    http://localhost:8000
    http://localhost:8000 real
