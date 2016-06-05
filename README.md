
# Product Database

*Version 0.3 (under development) - see [Changelog](CHANGELOG.md) for details*

This version is currently in development and contains multiple major changes to the underlying operating system and the
application . **Please note that an update path from Version 0.2 is not maintained.**

The following new features are planned/implemented:

* ~~change OS to Ubuntu 16.04 and to Django 1.9/Python 3.5~~
* ~~support of the Cisco EoX API Version 5.0~~
* ~~remove the Cisco Hello API dependency~~
* ~~new user interface~~
* ~~central notification panel~~
* ~~LDAP authentication backend~~
* save/provide Product Migration details from the Cisco EoX API
* add Slack integration for the notification panel
* implement process based import function (remove the 20000 entry limit)
* implement process based Bulk-EoL check function and make them persistent

Further ideas:

* add data from Cisco Product Information API (e.g. the )
* add web scraping component for data from other vendors

----

This web service provides a central point of management for product information, which is targeted primarily
for network products.

It currently focuses on the following use cases:

* automatic check of lifecycle states for a list of products against the local database (bulk EoL check)
* REST API access to a central database which holds information about products from network vendors
* import products using an Excel template (limited to 20000 records per Excel file)
* easy setup on a single Linux Server using Ansible

This web service is based on python 3.5.1 and Django 1.9. A detailed list with all dependencies is available in the
`requirements.txt` file.

## License

See the [license](LICENSE.md) file for license rights and limitations (MIT).

## Server requirements

* recommend 4 vCPU's
* min. 2 GB RAM

## Setup and Installation

### Local using Vagrant

This repository contains a Vagrant file that uses an Ansible playbook for installation. To try the Product Database
using Vagrant just clone the repository to a machine that runs [Vagrant](https://www.vagrantup.com/) and run the
following command within the code repository:

    $ vagrant up productdb

After a successful provisioning, the Product Database runs inside the VM and is available on **http://localhost:16000**.

### Server setup

To setup the **Product Database** on a server, you need a server running Ubuntu 16.04. Please note, that this web
service must be the only application running on the server. Within the `deploy` directory, you find a template directory
`stage_template` that contains an Ansible Playbook and a shell script.

To stage the machine, you need to clone this repository to an Ansible control node. On the target server, the code is
cloned as part of the Ansible playbook. Further details about ansible are available
[here](https://www.ansible.com/how-ansible-works).

The following steps are required to install the Product Database on a Server. You need to execute the following steps
after you've cloned the source code to the Ansible control machine:

 1. copy the `deploy/stage_template` to another directory (e.g. `deploy/stage_myserver`)
 2. edit the `ansible-inventory` file within the new directory (add the hostname and the username of your server)
 3. run the `stage-machine.sh` script from your staging directory

After the installation, there are two users created by default: one "pdb_admin" user with the password "admin", which can
be used for administration tasks and one "api" user with the password "api" for write actions on the REST API.
Any read action is permitted without authentication by default. To change this behavior, you can enable the "login-only
mode".

## Use the Cisco APIs within the Product Database

This version is capable to synchronize the local database with the Cisco EoX API. For more information about the Cisco
APIs see http://apiconsole.cisco.com for further details, Cisco Partner access only. Further details and descriptions
of this APIs are outlined at http://apiconsole.cisco.com. Please note the Terms & Conditions of this Service
(http://www.cisco.com/web/siteassets/legal/terms_condition.html).

To use the Product Database with the Cisco API console, you need to enter the client credentials on the settings page.
To run the test cases, please have a look at the development notes below.

These credentials can be created in the Cisco API administration. **Currently, the access permission to the
 Cisco EoX V5 API is required**

## development notes

Before running the test cases, you need access to the Cisco API console. Copy the file `conf/product_database.sample.config`
and rename it to `product_database.cisco_api_test.config`. Within this ini-like configuration file, add the your access
credentials within the `cisco_api` section on the keys `client_id` and `client_secret`.

I recommend to create a new **virtualenv** for development purpose. You can install the requirements using `pip` from the
`requirements.txt` and the `requirements_dev.txt` files.

All unit-tests can be executed using the module at `app.all_tests`. There are also some functional tests part of
this repository. They can be executed using the module `tests.functional_tests.all_functional_tests`. Futhermore, you
can run all tests using the module `tests.full_test_set`.

Every test case requires a local postgres database connection using the following parameters:

* the database name `productdb_dev`
* username `productdb`
* running at `localhost` port `5432`

Before you can start any test, you need to set the `DJANGO_SETTINGS_MODULE` variable:

```
$ export DJANGO_SETTINGS_MODULE=django_project.settings
$ python3 -m unittest app.all_tests
```
