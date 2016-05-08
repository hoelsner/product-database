from django_project.settings.common import *


def configure_logging(log_level, basedir, filename):
    U_LOGFILE_SIZE = 2 * 1024 * 1024
    U_LOGFILE_COUNT = 10
    #
    # configure development logging
    #
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
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
            'app': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': U_LOGFILE_SIZE,
                'backupCount': U_LOGFILE_COUNT,
                'filename': os.path.join(basedir, "app." + filename),
                'formatter': 'verbose',
            },
            'crawler': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': U_LOGFILE_SIZE,
                'backupCount': U_LOGFILE_COUNT,
                'filename': os.path.join(basedir, "crawler." + filename),
                'formatter': 'verbose',
            },
            'tasks': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': U_LOGFILE_SIZE,
                'backupCount': U_LOGFILE_COUNT,
                'filename': os.path.join(basedir, "tasks." + filename),
                'formatter': 'verbose',
            },
            'catch_all': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': U_LOGFILE_SIZE,
                'backupCount': U_LOGFILE_COUNT,
                'filename': os.path.join(basedir, "catch_all." + filename),
                'formatter': 'verbose',
            },
            'root': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': U_LOGFILE_SIZE,
                'backupCount': U_LOGFILE_COUNT,
                'filename': os.path.join(basedir, "root." + filename),
                'formatter': 'verbose',
            }
        },
        'loggers': {
            'app': {
                'handlers': ['console', 'app'],
                'level': log_level,
                'propagate': True,
            },
            'django_project': {
                'handlers': ['app'],
                'level': log_level,
                'propagate': True,
            },
            'app.productdb.extapi': {
                'handlers': ['crawler'],
                'level': log_level,
                'propagate': True,
            },
            'app.productdb.crawler': {
                'handlers': ['crawler'],
                'level': log_level,
                'propagate': True,
            },
            'app.productdb.tasks': {
                'handlers': ['tasks'],
                'level': log_level,
                'propagate': True,
            },
            '': {
                'handlers': ['catch_all'],
                'level': log_level,
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': ['catch_all'],
                'propagate': False,
                'level': log_level,
            }
        },
        'root': {
            'handlers': ['console', 'root'],
            'level': log_level,
            'propagate': True,
        }
    }

    return logging_config
