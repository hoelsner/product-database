# import the general settings for the project
from django_project.settings.common import *
from django_project.settings.logging import *
import logging

logger = logging.getLogger(__name__)
PDB_DEBUG = True if os.getenv("PDB_DEBUG") else False

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "PlsChgMe")

# configure database settings
DATABASE_NAME = os.getenv("PDB_DATABASE_NAME", "productdb_dev")
DATABASE_USER = os.getenv("PDB_DATABASE_USER", "productdb")
DATABASE_PASSWORD = os.getenv("PDB_DATABASE_PASSWORD", "productdb")
DATABASE_HOST = os.getenv("PDB_DATABASE_HOST", "127.0.0.1")
DATABASE_PORT = os.getenv("PDB_DATABASE_PORT", "5432")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT
    }
}

if PDB_DEBUG:
    DEBUG = True
    ALLOWED_HOSTS = []

else:
    ALLOWED_HOSTS = ["*"]
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

from django_project.settings.celery import *

"""
Configure logging settings
"""
DJANGO_LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')

# if debug mode is enabled in Django, also set the global logging level to Debug
if PDB_DEBUG:
    DJANGO_LOG_LEVEL = 'DEBUG'

log_file = os.path.join(BASE_DIR, "..", "..", "logs")
LOGGING = configure_logging(DJANGO_LOG_LEVEL, log_file, "product_db.log")

logging.getLogger().warn("DJANGO CONFIG: Start logging on level: %s" % DJANGO_LOG_LEVEL)

from django_project.settings.rest_framework import *
from django_project.settings.swagger_api import *
