# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-25 13:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0004_configoption'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configoption',
            name='value',
            field=models.CharField(blank=True, max_length=8192, null=True),
        ),
    ]