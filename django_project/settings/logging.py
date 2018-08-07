import os

DEFAULT_LOG_FORMAT_STRING = "[%(levelname)7s %(asctime)s] %(message)s"
DEFAULT_LOG_DATEFORMAT = "%d/%b/%Y %H:%M:%S"


def configure_logging(log_level, django_log_level, sentry_log_level, enable_sentry=False):
    #
    # configure django logging
    #
    logging_config = {
        "version": 1,
        "formatters": {
            "configured": {
                "format": os.environ.get("PDB_LOG_FORMAT", DEFAULT_LOG_FORMAT_STRING),
                "datefmt": os.environ.get("PDB_LOG_DATETIME_FORMAT", DEFAULT_LOG_DATEFORMAT)
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "configured",
            }
        },
        "loggers": {
            "productdb": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": True,
            },
            "django_auth_ldap": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": True,
            },
            "celery": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": True,
            },
            "raven": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "sentry": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "django": {
                "handlers": ["console"],
                "level": django_log_level,
                "propagate": False,
            },
            "": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            }
        }
    }

    if enable_sentry:
        logging_config["handlers"]["sentry"] = {
            "level": sentry_log_level,
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler"
        }
        for item in logging_config["loggers"].keys():
            logging_config["loggers"][item]["handlers"] += ["sentry"]

    return logging_config
