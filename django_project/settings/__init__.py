# import the general settings for the project
from django_project.settings.common import *
from django_project.settings.logging import *
import logging

logger = logging.getLogger(__name__)

try:
    # read secret key
    keyfile = os.path.join(BASE_DIR, "..", "..", "secret_key.key")
    if os.path.exists(keyfile):
        f = open(keyfile)
        SECRET_KEY = f.read()
    else:
        SECRET_KEY = "PlsChgMe"

except:
    SECRET_KEY = "PlsChgMe"
    logger.error("Django CONFIG: Default secret key not reconfigured, use '%s'" % SECRET_KEY)

# include production configuration (if available)
try:
    # deploy configuration requires a postgres server environment
    from django_project.settings.deploy import *

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

except:
    logger.warn("Django CONFIG: Deploy configuration not found, use development configuration")

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, "..", "db.sqlite3"),
        }
    }

    DEBUG = True
    ALLOWED_HOSTS = []

from django_project.settings.celery import *

"""
Configure logging settings
"""
level = os.getenv('DJANGO_LOG_LEVEL', 'INFO')

# if debug mode is enabled in Django, also set the global logging level to Debug
if DEBUG:
    level = 'DEBUG'

log_file = os.path.join(BASE_DIR, "..", "..", "logs")
LOGGING = configure_logging(level, log_file, "product_db.log")

logging.getLogger().warn("DJANGO CONFIG: Start logging on level: %s" % level)

from django_project.settings.rest_framework import *
from django_project.settings.swagger_api import *
