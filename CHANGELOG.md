# changelog

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