
# Product Database

*Version 0.3 (development) - see [Changelog](CHANGELOG.md) for details*

This version is currently in development and contains multiple major changes to the underlying operating system and the
application . **Please note that an update path from Version 0.2 is not maintained.**

The following new features are planned/implemented:

* ~~change OS to Ubuntu 16.04 and to Django 1.9/Python 3.5~~
* ~~support of the Cisco EoX API Version 5.0~~
* ~~remove the Cisco Hello API dependency~~
* ~~new user interface~~
* ~~central notification panel~~
* ~~LDAP authentication backend~~
* ~~implement process based import function (remove the 20000 entry limit)~~
* add Product Groups
* save/provide Product Migration details from the Cisco EoX API
* add lifecycle data to the import product function
* add Slack notifications to send messages about the status of the Product Database (errors, crawler execution results...)
* implement process based Bulk-EoL check function and store the results in the database
* additional data from Cisco Product Information API (e.g. the Product Group, link to the support page etc.)
* add web scraping component

----

This web service provides a central point of management for product information, which is targeted primarily
for network products. It currently focuses on the following use cases:

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

## Product Database Installation

The entire setup of the Product Database is based on an Ansible playbook. This playbook contains all parameters and setup
to setup a new instance of the web-service. There are multiple ways to deploy a new instance of the Product Database:

* Dedicated Server setup (without an Ansible control machine)
* Dedicated Server setup (using an Ansible control machine)
* Vagrant VM

Two users are created during the installation process: one superuser with the username **pdb_admin** and the
password **pdb_admin** and one **api** user with the password **api** as a normal user. Any read action on the web-site
is permitted without authentication by default. To change this behavior, you can enable the "login-only mode". The
REST API is only available to registered users.

### Dedicated Server setup

To setup the **Product Database** on a dedicated server, you need a clean installation of Ubuntu 16.04. Please note, that
this web service must be the only application running on the server. Within the `deploy` directory, you find an
installation profile with some predefined default values named `stage_default`. The entire setup is based on an Ansible
playbook.

### Setup without an Ansible control machine

The following steps are required if you have only a single Ubuntu 16.04 server that should run the Product Database.
First, you need to install the following dependencies:

```
sudo apt-get install python python-dev python3 python-pip python3-pip git openssh-server build-essential libssl-dev libffi-dev sshpass
sudo -H pip install ansible
sudo -H pip3 install invoke
```

After a successful installation of these packages, clone the code from GitHub and navigate to the `stage_default` directory:

```
git clone https://github.com/hoelsner/product-database.git
cd product-database/deploy/stage_default
```

Now you can start the installation on the local host using the following command:

```
invoke deploy_local -u <username> -p <password>
```

Please note that the user must be permitted to use SSH (to get Ansible working). Furthermore, this user requires sudo
permissions and is used to run the application as a service.

#### Setup using an Ansible control node

Before you start the setup process, please make sure that the following requirements are satisfied on your Ubuntu Server:

  * python Version 2 is installed (required to run Ansible)
  * the deployment user is also used to run the required services
  * the deployment user requires sudo permissions

You need an Ansible control machine to deploy your dedicated server (Linux/Mac OS X only, see
[the Ansible installation guide for details](http://docs.ansible.com/ansible/intro_installation.html#installing-the-control-machine)).
On the Ansible control machine, you need to perform the following steps:

 1. install python2 ,ansible and invoke
 2. clone the code repository from GitHub
 3. run the invoke deploy task (just a task runner to simplify the execution)

```
sudo -H pip3 install invoke
git clone https://github.com/hoelsner/product-database.git
cd deploy/stage_default
invoke deploy <ip/hostname> -u <username> -p <password>
```

The `password` is only required if you're using SSH password-based authentication.

### Vagrant VM

This repository contains a Vagrant file that describes a Product Database VM for testing, demo and development purpose.
To create a VM using Vagrant, you simply need to clone (or copy) the repository to your laptop.
Before continue, you need to install [Vagrant](https://www.vagrantup.com/) and a an virtualization software like VirtualBox.
You need to run the following command within the local code repository:

    $ vagrant up productdb

After a successful provisioning process, the Product Database runs inside the VM and is available on
**http://localhost:16000**.

# Cisco APIs within the Product Database

This version is capable to synchronize the local database with the Cisco EoX API. For more information about the Cisco
APIs see [http://apiconsole.cisco.com](http://apiconsole.cisco.com) for further details, Cisco Partner access only.
Further details and descriptions of this APIs are outlined at http://apiconsole.cisco.com. Please note the Terms &
Conditions of this Service
([http://www.cisco.com/web/siteassets/legal/terms_condition.html](http://www.cisco.com/web/siteassets/legal/terms_condition.html)).

To use the Product Database with the Cisco API console, you need to enter the client credentials on the settings page.
To run the test cases, please have a look at the development notes below.

These credentials can be created in the Cisco API administration. **Currently, the access permission to the
 Cisco EoX V5 API is required**

# Development Notes

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
