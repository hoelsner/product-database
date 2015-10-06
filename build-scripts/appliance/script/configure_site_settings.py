#!/usr/bin/env python3
import os
import random
import sys
"""
configure a site on the server, executed by the Ansible playbook

requires two parameters:
  python3 configure_site_settings.py <sitename> <username> <dbname> [production] [ignore_allowhosts]
"""

#
# set variables
#
settings_path = "../../../django_project/settings/common.py"
deploy_configuration = "../../../django_project/settings/deploy.py"

try:
    # 0 is the filename
    site_name = sys.argv[1]
    site_user = sys.argv[2]
    dbname = sys.argv[3]

    if sys.argv[4] == "production":
        is_production = True
        if sys.argv[5] == "True":
            ignore_allowhosts = True
        else:
            ignore_allowhosts = False
    else:
        is_production = False
        if sys.argv[4] == "True":
            ignore_allowhosts = True
        else:
            ignore_allowhosts = False

except:
    print("Use the following format:\n   python3 configure_site_settings.py <sitename> <username> [production] [ignore_allowhosts]")
    sys.exit(1)

print("site_name set to %s" % site_name)
print("site_user set to %s" % site_user)
print("deploy in production: %s" % is_production)
print("ignore allowed hosts set to %s" % ignore_allowhosts)

#
# configure security settings when production environment is deployed, otherwise enable debugging
#
result = "# deployment configuration --- automatic\n"
if is_production:
    result += "DEBUG = False\n"
    if not ignore_allowhosts:
        result += 'ALLOWED_HOSTS = [ "%s" ]\n' % (site_name)
    else:
        result += 'ALLOWED_HOSTS = [ "*" ]\n'
else:
    result += "DEBUG = True\n"
#
# create secret_key_file
#
secret_key_file = '../../../../secret_key.key'
if not os.path.exists(secret_key_file):
    chars = "ajsdoahrguhru9ghaonaeorut3lnuvhlegsidlnaoevgu4n89znn9a3l7gmx4nfhuvguaegnmcs"
    key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
    f = open(secret_key_file, "w")
    f.write(key)
    f.close()

else:
    # read the key (required for DB configuration)
    f = open(secret_key_file, "r")
    key = f.read()
    f.close()

print("key set to %s" % key)

#
# configure postgres database
#
result += "DATABASES = {" \
              "'default': {" \
                "'ENGINE': 'django.db.backends.postgresql_psycopg2'," \
                "'NAME': '%s_database'," \
                "'USER': '%s'," \
                "'PASSWORD': '%s'," \
                "'HOST': 'localhost'," \
                "'PORT': ''," \
            "}" \
        "}" % (dbname, site_user, key)

#
# save deployment configuration
#
f = open(deploy_configuration, "w")
f.write(result)
f.close()

