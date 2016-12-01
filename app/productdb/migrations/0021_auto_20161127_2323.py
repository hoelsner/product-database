# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('productdb', '0020_auto_20161122_2236'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCheck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name to identify the Product Check', max_length=256, verbose_name='Name')),
                ('input_product_ids', models.TextField(help_text='unordered Product IDs, separated by line breaks or semicolon', max_length=32768, verbose_name='Product ID list')),
                ('last_change', models.DateTimeField(auto_now=True)),
                ('task_id', models.CharField(blank=True, help_text='if set, the product check is currently executed', max_length=64, null=True)),
                ('create_user', models.ForeignKey(blank=True, help_text='if not null, the product check is available to all users', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('migration_source', models.ForeignKey(blank=True, help_text='migration source to identify the replacement options, if not selected the preferred migration path is used', null=True, on_delete=django.db.models.deletion.CASCADE, to='productdb.ProductMigrationSource', verbose_name='migration source')),
            ],
        ),
        migrations.CreateModel(
            name='ProductCheckEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_product_id', models.CharField(max_length=256, verbose_name='Product ID')),
                ('amount', models.PositiveIntegerField(default=0, verbose_name='amount')),
                ('migration_product_id', models.CharField(blank=True, default='', max_length=256, verbose_name='Migration Option')),
                ('part_of_product_list', models.CharField(blank=True, default='', help_text='hash values of product lists that contain the Product (at time of the check)', max_length=512, verbose_name='product list hash values')),
                ('product_check', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='productdb.ProductCheck')),
                ('product_in_database', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='productdb.Product')),
            ],
        ),
        migrations.AddField(
            model_name='productlist',
            name='hash',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
