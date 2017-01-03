# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productdb', '0023_userprofile_choose_migration_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='choose_migration_source',
            field=models.BooleanField(default=False, help_text="specify the Migration Source for a Product Check (don't use the preferred migration path)", verbose_name='choose Migration Source in Product Check'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='regex_search',
            field=models.BooleanField(default=False, help_text='Use regular expression in any search field (fallback to simple search if no valid regular expression is used)', verbose_name='use regular expressions in search fields'),
        ),
    ]
