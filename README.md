
# Product Database

*Version 0.9 (development) - see [changelog](CHANGELOG.md) for details*

This web service provides a central point of management for product information. The current focus are the lifecycle data (EoL checks) for network products.

The following use-cases are implemented:

* automatic check of the lifecycle state for a list of products against the local database (Product Check)
* synchronization with the Cisco EoX API
* REST API to access the data stored in the application
* manual data maintenance using Excel

This web service is based on python 3.5 and Django 1.11. A detailed list with all dependencies is available in the `requirements.txt` file.

## Setup & Installation

See the [Setup & Installation](SETUP.md) file for details.

## License

See the [license](LICENSE.md) file for license rights and limitations (MIT).

## Cisco EoX APIs (Cisco Support APIs) within the Product Database

This version is capable to synchronize the local database with the Cisco EoX API. More information about the API is available at [http://apiconsole.cisco.com](http://apiconsole.cisco.com) (Cisco Partner access only). Please note the Terms & Conditions of this Service ([http://www.cisco.com/web/siteassets/legal/terms_condition.html](http://www.cisco.com/web/siteassets/legal/terms_condition.html)).
