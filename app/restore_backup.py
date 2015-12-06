"""
script, that restores a backup of the following elements to the database:

* Products
* Product lists

It will take the backup-files from the ../backup directory and must be executed at the django project root directory

"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

import django

django.setup()

from app.productdb.model_backup import restore_backup

BACKUP_DIRECTORY = os.path.join("..", "backup")

if __name__ == '__main__':
    restore_backup(BACKUP_DIRECTORY)
