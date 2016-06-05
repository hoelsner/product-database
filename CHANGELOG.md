# changelog

## Version 0.3 (under development)

* complete redesign of the user interface
* add the login only-mode setting (the site requires always a login, not only for the administrative tasks)
* removed some (almost unused) features, including the custom product lists and the simple backup mechanism
* Update of the target Cisco EoX API to Version 5 (includes the "End of Vulnerability/Security Support date")
* optional LDAP authentication

## Version 0.2

* import products using an Excel file (limited to 20000 entries per file)
* add basic backup/restore implementation
* move all components of the webservice (Django admin, static files) to the `/productdb` URL

## Version 0.1

initial release which includes the following features:

* integration of the Cisco API crawler
* integration of a bulk EoL check tool
* initial version of the Product Database API