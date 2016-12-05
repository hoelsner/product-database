"""
WSGI config for the Django project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import djcelery
from django.core.wsgi import get_wsgi_application
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry

os.environ["CELERY_LOADER"] = "django"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")
djcelery.setup_loader()

if os.getenv("PDB_ENABLE_SENTRY"):
    application = Sentry(get_wsgi_application())

else:
    application = get_wsgi_application()
