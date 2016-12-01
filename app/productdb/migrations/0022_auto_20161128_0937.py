# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('productdb', '0021_auto_20161127_2323'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productcheckentry',
            name='migration_product_id',
        ),
        migrations.AddField(
            model_name='productcheckentry',
            name='migration_product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='productdb.ProductMigrationOption', verbose_name='Migration Option'),
        ),
        migrations.AlterField(
            model_name='productcheck',
            name='input_product_ids',
            field=models.TextField(help_text='unordered Product IDs, separated by line breaks or semicolon', max_length=65536, verbose_name='Product ID list'),
        ),
    ]
