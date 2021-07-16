import os
import raven
import logging as _logging

logger = _logging.getLogger()

PDB_DEBUG = True if os.getenv("PDB_DEBUG") else False

if PDB_DEBUG:
    DEBUG = True
    ALLOWED_HOSTS = ["*"]

else:
    ALLOWED_HOSTS = os.environ.get("PDB_ALLOWED_HOSTS", "*").split(";") \
                     if os.environ.get("PDB_ALLOWED_HOSTS", "*") != "*" \
                     else ["*"]
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

# import the general settings for the project
from django_project.settings.common import *
from django_project.settings.logging import configure_logging
from django_project.settings.celery import *

"""
Configure logging settings
"""
DJANGO_LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "DEBUG" if PDB_DEBUG else "INFO").upper()
if os.getenv("PDB_TESTING", False):
    DJANGO_LOG_LEVEL = "DEBUG"

# if debug mode is enabled in Django, also set the global logging level to Debug
if PDB_DEBUG:
    DJANGO_LOG_LEVEL = "DEBUG"

PDB_SENTRY_DSN = os.getenv("PDB_SENTRY_DSN", None)

if PDB_SENTRY_DSN:
    INSTALLED_APPS += ["raven.contrib.django.raven_compat"]
    RAVEN_CONFIG = {
        "dsn": PDB_SENTRY_DSN,
        "release": raven.fetch_git_sha(os.path.dirname(os.pardir)),
    }
    if PDB_DEBUG:
        print("enable Sentry logging...")

LOGGING = configure_logging(
    DJANGO_LOG_LEVEL,
    django_log_level=os.environ.get("PDB_DJANGO_LOG_LEVEL", "INFO" if PDB_DEBUG else "WARNING"),
    sentry_log_level=os.environ.get("PDB_SENTRY_LOG_LEVEL", "DEBUG" if PDB_DEBUG else "WARNING"),
    enable_sentry=True if PDB_SENTRY_DSN else False
)

if PDB_DEBUG:
    logger.warning("DJANGO CONFIG: Start logging on level: %s" % DJANGO_LOG_LEVEL)

from django_project.settings.rest_framework import *
from django_project.settings.ldap import *
from django_project.settings.swagger_api import *
