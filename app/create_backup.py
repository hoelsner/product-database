"""
script, that creates a backup of the following elements within the database:

* Products
* Product lists

It will create the backup-files within the ../backup directory and must be executed at the django project root directory

"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

import django

django.setup()

from app.productdb.model_backup import create_backup

BACKUP_DIRECTORY = os.path.join("..", "backup")

if __name__ == '__main__':
    create_backup(BACKUP_DIRECTORY)
