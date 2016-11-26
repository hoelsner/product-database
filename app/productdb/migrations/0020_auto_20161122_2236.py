# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import app.productdb.validators
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productdb', '0019_productmigrationoption_replacement_db_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='list_price_timestamp',
            field=models.DateField(blank=True, help_text='last change of the list price', null=True, verbose_name='list price timestamp'),
        ),
        migrations.AddField(
            model_name='product',
            name='update_timestamp',
            field=models.DateField(auto_created=True, auto_now=True, default=datetime.datetime(2016, 1, 1, 0, 0), help_text='last changes to the product data', verbose_name='update timestamp'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productlist',
            name='description',
            field=models.TextField(blank=True, help_text="short description what's part of this Product List (markdown and/or HTML)", max_length=4096, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='productlist',
            name='string_product_list',
            field=models.TextField(help_text='Product IDs separated by word wrap or semicolon', max_length=16384, validators=[app.productdb.validators.validate_product_list_string], verbose_name='Unstructured Product IDs separated by line break'),
        ),
        migrations.AlterField(
            model_name='productlist',
            name='version_note',
            field=models.TextField(blank=True, help_text='some version information for the product list (markdown and/or HTML)', max_length=16384, verbose_name='Version note'),
        ),
    ]
