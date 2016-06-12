"""
common Django settings for project
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("Django BASE_DIR: %s" % BASE_DIR)

INSTALLED_APPS = (
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
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'reversion.middleware.RevisionMiddleware',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'product_database_cache_table',
    }
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
            ],
        },
    },
]

WSGI_APPLICATION = 'django_project.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGIN_URL = "/productdb/login/"
LOGOUT_URL = "/productdb/logout/"
LOGIN_REDIRECT_URL = "/productdb/"

STATIC_URL = '/productdb/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '../../static'))
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "../static"),
    os.path.join(BASE_DIR, "../node_modules"),
)

# demo mode only for testing
DEMO_MODE = False

# enable session timeout
SESSION_COOKIE_AGE = 60 * 15
SESSION_SAVE_EVERY_REQUEST = True

# name of the configuration file that should be used
APP_CONFIG_FILE = os.path.join("conf", os.getenv("PDB_CONFIG_FILE", "product_database.config"))

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
