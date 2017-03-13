from django_project.settings.common import *


def configure_logging(log_level, basedir, filename, enable_sentry=False):
    u_logfile_size = 2 * 1024 * 1024
    u_logfile_count = 5
    #
    # configure development logging
    #
    logging_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '[%(levelname)s %(asctime)s] %(module)s %(process)d %(thread)d %(message)s',
                'datefmt': "%d/%b/%Y %H:%M:%S"
            },
            'regular': {
                'format': '[%(levelname)s %(asctime)s] [%(module)s] %(message)s',
                'datefmt': "%d/%b/%Y %H:%M:%S"
            },
            'simple': {
                'format': '[%(levelname)s %(asctime)s] [%(module)s] %(message)s',
                'datefmt': "%H:%M:%S"
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'productdb': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': u_logfile_size,
                'backupCount': u_logfile_count,
                'filename': os.path.join(basedir, "app." + filename),
                'formatter': 'verbose',
            },
            'django_logfile': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': u_logfile_size,
                'backupCount': u_logfile_count,
                'filename': os.path.join(basedir, "django." + filename),
                'formatter': 'verbose',
            },
            'catch_all': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': u_logfile_size,
                'backupCount': u_logfile_count,
                'filename': os.path.join(basedir, "catch_all." + filename),
                'formatter': 'verbose',
            },
            'root': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': u_logfile_size,
                'backupCount': u_logfile_count,
                'filename': os.path.join(basedir, "root." + filename),
                'formatter': 'verbose',
            }
        },
        'loggers': {
            'productdb': {
                'handlers': ['console', 'productdb'],
                'level': log_level,
                'propagate': True,
            },
            '': {
                'handlers': ['console', 'catch_all'],
                'level': log_level,
                'propagate': True,
            },
            'django': {
                'handlers': ['console', 'django_logfile'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['catch_all'],
                'propagate': False,
                'level': log_level,
            },
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
            'sentry.errors': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
            'celery': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            }
        },
        'root': {
            'handlers': ['console', 'root'],
            'level': log_level,
            'propagate': True,
        }
    }

    if enable_sentry:
        logging_config["handlers"]["sentry"] = {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler'
        }
        logging_config["loggers"]["productdb"]["handlers"] += ["sentry"]
        logging_config["loggers"]["celery"]["handlers"] += ["sentry"]
        logging_config["loggers"][""]["handlers"] += ["sentry"]

    return logging_config
