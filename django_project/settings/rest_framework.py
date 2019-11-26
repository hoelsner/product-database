import os


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework_xml.renderers.XMLRenderer"
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoObjectPermissions"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "COMPACT_JSON": False if os.getenv("COMPACT_JSON", False) else False,
    "UNICODE_JSON": True,
    "DEFAULT_PAGINATION_CLASS": "django_project.pagination.CustomPagination",
    "PAGE_SIZE": 25,
}
USE_X_FORWARDED_HOST = True
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "basic": {
            "type": "basic"
        },
        "api_key": {
            "type": "apiKey",
            "name": "Token",
            "in": "header"
        },
    },
    "REFETCH_SCHEMA_ON_LOGOUT": True,
    "REFETCH_SCHEMA_WITH_AUTH": True,
    "VALIDATOR_URL": ""
}
