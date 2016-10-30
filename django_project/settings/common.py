"""
common Django settings for project
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("Django BASE_DIR: %s" % BASE_DIR)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'bootstrap3',
    'reversion',
    'reversion_compare',
    'app.productdb',
    'app.config',
    'app.ciscoeox',
    'cacheops',
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'reversion.middleware.RevisionMiddleware',
]

if os.getenv("PDB_DEBUG"):
    print("Use database caching and disable cacheops...")
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'product_database_cache_table',
        }
    }
    CACHEOPS_ENABLED = False  # disable cacheops for debugging

else:
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': 'localhost:6379',
        },
    }
    CACHEOPS_REDIS = {
        'host': 'localhost',
        'port': 6379,
        'socket_timeout': 3,
    }
    CACHEOPS_DEFAULTS = {
        'timeout': 60 * 60
    }
    CACHEOPS = {
        'auth.user': {'ops': 'get', 'timeout': 60*15},
        'auth.*': {'ops': ('fetch', 'get')},
        'auth.permission': {'ops': 'all'},
        'productdb.Vendor': {'ops': 'get'},
        'productdb.Product': {'ops': 'all'},
        'productdb.ProductGroup': {'ops': 'all'},
        'productdb.ProductMigrationOption': {'ops': 'all'},
        'productdb.ProductMigrationSource': {'ops': 'all'},
        'productdb.ProductList': {'ops': 'all'},
    }

ROOT_URLCONF = 'django_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_project.context_processors.is_ldap_authenticated_user',
                'django_project.context_processors.get_internal_product_id_label',
            ],
        },
    },
]

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

WSGI_APPLICATION = 'django_project.wsgi.application'

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
CSRF_FAILURE_VIEW = 'django_project.views.custom_csrf_failure_page'

STATIC_URL = '/productdb/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '../../static'))
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "../static"),
    os.path.join(BASE_DIR, "../node_modules"),
)

# enable session timeout
SESSION_COOKIE_AGE = 60 * 15
SESSION_SAVE_EVERY_REQUEST = True

BOOTSTRAP3 = {
    'jquery_url': 'lib/jquery/dist/jquery.min.js',
    'base_url': 'lib/bootstrap/dist',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'javascript_in_head': False,
    'include_jquery': False,
    'horizontal_label_class': 'col-md-3',
    'horizontal_field_class': 'col-md-9',
    'set_required': True,
    'set_disabled': False,
    'set_placeholder': False,
    'required_css_class': '',
    'error_css_class': 'has-error',
    'success_css_class': 'has-success',
}


DATA_DIRECTORY = os.path.join("data")

if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY, exist_ok=True)

ADD_REVERSION_ADMIN = True

if os.getenv("PDB_DEBUG"):
    # enable django debug toolbar (only installed with the dev requirements)
    INTERNAL_IPS = ["127.0.0.1"]
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Force HTTPs (should be used in production)
if os.getenv("PDB_HTTPS_ONLY", False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
