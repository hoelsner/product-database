import os

PDB_DEBUG = True if os.getenv("PDB_DEBUG") else False

# import the general settings for the project
from django_project.settings.common import *
from django_project.settings.logging import *
import logging

logger = logging.getLogger(__name__)

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
from django_project.settings.ldap import *
from django_project.settings.swagger_api import *
