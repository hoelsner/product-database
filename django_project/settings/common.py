"""
common Django settings for project
"""
import os
import logging as _logging

logger = _logging.getLogger()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.getenv("PDB_DEBUG", False):
    logger.warning("DJANGO CONFIG: Django BASE_DIR: %s" % BASE_DIR)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_yasg",
    "rest_framework.authtoken",
    "django_celery_beat",
    "django_celery_results",
    "bootstrap3",
    "app.productdb",
    "app.config",
    "app.ciscoeox",
    "cacheops",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware"
]

if os.getenv("PDB_DEBUG", False) and os.getenv("PDB_DEBUG_NO_CACHE", False):
    logger.warning("DJANGO CONFIG: use database caching and disable cacheops...")
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "product_database_cache_table",
        }
    }
    CACHEOPS_ENABLED = False  # disable cacheops for debugging

else:
    redis_server = os.environ.get("PDB_REDIS_HOST", "127.0.0.1")
    redis_port = os.environ.get("PDB_REDIS_PORT", "6379")
    redis_pass = os.environ.get("PDB_REDIS_PASSWORD", "PlsChgMe")
    CACHES = {
        "default": {
            "BACKEND": "redis_cache.RedisCache",
            "LOCATION": "%s:%s" % (redis_server, redis_port),
            "OPTIONS": {
                "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
                "CONNECTION_POOL_CLASS_KWARGS": {
                    "max_connections": 50,
                    "timeout": 20,
                }
            }
        },
    }
    if redis_pass:
        CACHES["default"]["OPTIONS"]["PASSWORD"] = redis_pass

    if os.getenv("PDB_DISABLE_CACHEOPS", False):
        logger.warning("DJANGO CONFIG: use redis caching and disable cacheops...")
        CACHEOPS_ENABLED = False  # disable cacheops for debugging

    else:
        CACHEOPS_REDIS = {
            "host": redis_server,
            "port": redis_port,
            "socket_timeout": 10,
        }
        if redis_pass:
            CACHEOPS_REDIS["password"] = redis_pass

        CACHEOPS_DEFAULTS = {
            "timeout": 4 * 60 * 60
        }
        CACHEOPS = {
            "auth.*": {},
            "auth.user": {
                "ops": "all",
                "timeout": 15 * 60
            },
            "productdb.ProductList": {
                "ops": "all",
                "timeout": 48 * 60 * 60
            },
            "config.*": {
                "ops": "all",
                "timeout": 24 * 60 * 60
            },
            "*.*": {
                "ops": "all"
            },
        }

ROOT_URLCONF = "django_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "../templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_project.context_processors.is_ldap_authenticated_user",
                "django_project.context_processors.get_internal_product_id_label"
            ],
        },
    },
]

if os.getenv("PDB_DEBUG", False) or os.getenv("DEBUG", False):
    TEMPLATES[0]["OPTIONS"]["context_processors"].append("django_project.context_processors.is_debug_enabled")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "PlsChgMe")

# configure database settings
DATABASE_NAME = os.getenv("PDB_DATABASE_NAME", os.getenv("POSTGRES_DB", "productdb"))
DATABASE_USER = os.getenv("PDB_DATABASE_USER", os.getenv("POSTGRES_USER", "postgres"))
DATABASE_PASSWORD = os.getenv("PDB_DATABASE_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
DATABASE_HOST = os.getenv("PDB_DATABASE_HOST", "127.0.0.1")
DATABASE_PORT = os.getenv("PDB_DATABASE_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
        "OPTIONS": {
            "sslmode": os.getenv(
                "PDB_DATABASE_SSLMODE",
                "require" if not os.getenv("PDB_DEBUG", False) and not os.getenv("PDB_TESTING", False) else "prefer"
            ),
            "sslcert": os.getenv("PDB_DATABASE_SSLCERT", "/var/www/productdb/ssl/database.crt"),
            "sslkey": os.getenv("PDB_DATABASE_SSLKEY", "/var/www/productdb/ssl/database.key")
        },
    }
}

# HTTP proxy setting used with the Cisco Support API
HTTP_PROXY_SERVER = os.getenv("PDB_HTTP_PROXY", None)
HTTPS_PROXY_SERVER = os.getenv("PDB_HTTPS_PROXY", None)
WSGI_APPLICATION = "django_project.wsgi.application"

LANGUAGE_CODE = os.getenv("PDB_LANGUAGE_CODE", "en-us")
TIME_ZONE = os.getenv("PDB_TIME_ZONE", "Europe/Berlin")
USE_I18N = False
USE_L10N = False
USE_TZ = True

TIME_FORMAT = os.getenv("PDB_TIME_FORMAT", "P")
DATE_FORMAT = os.getenv("PDB_DATE_FORMAT", "N j, Y")
SHORT_DATE_FORMAT = os.getenv("PDB_SHORT_DATE_FORMAT", "Y-m-d")
DATETIME_FORMAT = os.getenv("PDB_DATETIME_FORMAT", DATE_FORMAT + ", " + TIME_FORMAT)
SHORT_DATETIME_FORMAT = os.getenv("PDB_SHORT_DATETIME_FORMAT", SHORT_DATE_FORMAT + " " + TIME_FORMAT)

LOGIN_URL = "/productdb/login/"
LOGOUT_URL = "/productdb/logout/"
LOGIN_REDIRECT_URL = "/productdb/"
CSRF_FAILURE_VIEW = "django_project.views.custom_csrf_failure_page"

STATIC_URL = "/productdb/static/"
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "static"))
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "..", "static"),
)

if os.getenv("PDB_SESSION_EXPIRE_ON_BROWSER_CLOSE", None):
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_AGE = os.getenv("SESSION_COOKIE_AGE", 60 * 60)

else:
    SESSION_COOKIE_AGE = os.getenv("SESSION_COOKIE_AGE", 60 * 60)
    SESSION_SAVE_EVERY_REQUEST = True

SESSION_COOKIE_NAME = "productdb"
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

BOOTSTRAP3 = {
    "jquery_url": "lib/jquery/dist/jquery.min.js",
    "base_url": "lib/bootstrap/dist",
    "css_url": None,
    "theme_url": None,
    "javascript_url": None,
    "javascript_in_head": False,
    "include_jquery": False,
    "horizontal_label_class": "col-md-3",
    "horizontal_field_class": "col-md-9",
    "set_required": True,
    "set_disabled": False,
    "set_placeholder": False,
    "required_css_class": "",
    "error_css_class": "has-error",
    "success_css_class": "has-success",
}

DATA_DIRECTORY = os.path.join(os.path.join("..", "data"))
MEDIA_ROOT = DATA_DIRECTORY

# install data directory if required
if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY, exist_ok=True)

ADD_REVERSION_ADMIN = True

if os.getenv("PDB_DEBUG"):
    from ipaddress import IPv4Interface
    # enable django debug toolbar (only installed with the dev requirements)
    debug_ip = os.getenv("DEBUG_IP", "127.0.0.1/32")
    INTERNAL_IPS = [str(host) for host in IPv4Interface(debug_ip).network]
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    if os.getenv("DISABLE_ASYNC_TASKS", False):
        CELERY_ALWAYS_EAGER = True
        CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Force HTTPs (always used in production) - disable for testing using the environment variable PDB_TESTING=1
if not os.getenv("PDB_DEBUG") and not os.getenv("PDB_TESTING", False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_AGE = 60 * 60 * 24 * 30
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
