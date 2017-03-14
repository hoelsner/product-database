# changelog

## Version 0.5 (development)

* add ```show inventory``` parser to the new Product Check
* preferred migration options must have a preference greater than 25
* REST API authentication is now possible with user specific tokens (available in the User Profile, 
[see Django REST framework for details](http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication)) 
* the input Product IDs field in the Product Check has now an unlimited length
* the web-service now notifies a super user, if no backend worker is active/registered
* **HTTPs is now mandatory**
* **add Dockerfile**

## Version 0.4

**Before updating from Version 0.3 to Version 0.4, please save your current configuration values. Version 0.4 
stores the configuration values in the database, not the configuration file. After the update, you must reconfigure 
the Product Database settings.**

* add new **Product Check** (enhanced version of the Bulk EoL Check)
  * persistent version of the earlier Bulk-EoL-check
  * improved presentation of the results
  * public (for all users) or private visibility
  * recursive lookup of replacement options ()
* add **User Profile** for authenticated users
  * change eMail that is stored in the database
  * select a preferred vendor (default for the "view vendor products" list)
  * choose between a simple contain based and regex search (like or regular expressions) - see [issue #3](https://github.com/hoelsner/product-database/issues/3)
* additional configuration options during the build
  * optional **HTTPs deployment** (using a self-signed or custom certificate)
  * optional **LDAP authentication**
* data model changes
  * add "automatic synchronized" flag to Product entries (if synchronization with the Cisco EoX API is enabled)
  * add Internal Product ID label to Products with a configurable UI label
  * add Product Migration Options to the database
  * add version note to Product List
* backend changes
  * add cache implementation (based on [django-cacheops](https://github.com/Suor/django-cacheops) and redis)
  * add sentry logging (optional)
  * django settings are now stored in a single configuration file (```/etc/productdb/productdb```)
  * moved the application configuration values to the database, removed the separate configuration file

## Version 0.3

* complete redesign of the user interface
* add the login only-mode setting (the site requires always a login, not only for the administrative tasks)
* removed some (almost unused) features, including the simple backup mechanism
* rewrite the custom Product List implementation
* add detail view for Products
* Update of the target Cisco EoX API to Version 5 (includes the "End of Vulnerability/Security Support date")
* add optional LDAP authentication
* extend the import products using Excel feature:
  * remove the import product limitation
  * add additional fields on import (e.g. EoS data)
  * add create Notification Message option
  * add update only existing Products option
* API changes
  * authentication now always required
  * use Django object permissions
  * search and filtering now possible as GET parameter
* add some basic permissions
  * import product now allowed with the `productdb.change_product` permission (only the superuser is allowed to add a notification message)
  * the add, change and delete options for the Product List are in use

## Version 0.2

* import products using an Excel file (limited to 20000 entries per file)
* add basic backup/restore implementation
* move all components of the webservice (Django admin, static files) to the `/productdb` URL

## Version 0.1

initial release which includes the following features:

* integration of the Cisco API crawler
* integration of a bulk EoL check tool
* initial version of the Product Database API
