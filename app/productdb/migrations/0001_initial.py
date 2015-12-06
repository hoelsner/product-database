# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import app.productdb.validators
import django.core.validators
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CiscoApiAuthSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('api_client_id', models.TextField(help_text='Client ID for the Cisco API authentication', default='PlsChgMe', blank=True)),
                ('api_client_secret', models.TextField(help_text='Client Secret for the Cisco API authentication', default='PlsChgMe', blank=True)),
                ('cached_http_auth_header', models.TextField(help_text='cached authentication header with expire date in JSON format', default='', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('product_id', models.TextField(help_text='Unique Product ID', unique=True)),
                ('description', models.TextField(help_text='description of the product', default='not set')),
                ('list_price', models.DecimalField(help_text='list price of the element', validators=[django.core.validators.MinValueValidator(0)], null=True, blank=True, max_digits=32, decimal_places=2)),
                ('currency', models.TextField(help_text='currency of the list price', default='USD', choices=[('EUR', 'Euro'), ('USD', 'US-Dollar')], max_length=16)),
                ('tags', models.TextField(help_text='unformatted tag field', default='', blank=True)),
                ('json_data', annoying.fields.JSONField(help_text='free JSON data (will be delivered with the meta API endpoint', validators=[app.productdb.validators.validate_json], null=True, blank=True)),
                ('eox_update_time_stamp', models.DateField(help_text='EoX lifecycle data update time stamp (set with automatic synchronization)', null=True, blank=True)),
                ('eol_ext_announcement_date', models.DateField(help_text='external EoX announcement date', null=True, blank=True)),
                ('end_of_sale_date', models.DateField(help_text='End of Sale date', null=True, blank=True)),
                ('end_of_new_service_attachment_date', models.DateField(help_text='End of new Service Attachment date', null=True, blank=True)),
                ('end_of_sw_maintenance_date', models.DateField(help_text='End of Software Maintenance date', null=True, blank=True)),
                ('end_of_routine_failure_analysis', models.DateField(help_text='End of Routine Failure analysis', null=True, blank=True)),
                ('end_of_service_contract_renewal', models.DateField(help_text='End of Service Contract renewal date', null=True, blank=True)),
                ('end_of_support_date', models.DateField(help_text='End of Support (Last day of support) date', null=True, blank=True)),
                ('eol_reference_number', models.TextField(help_text='Product bulletin number or vendor specific reference for EoL', null=True, blank=True)),
                ('eol_reference_url', models.URLField(help_text='URL to the Product bulletin or EoL reference', null=True, blank=True)),
            ],
            options={
                'ordering': ('product_id',),
            },
        ),
        migrations.CreateModel(
            name='ProductList',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('product_list_name', models.TextField(max_length=128, unique=True)),
                ('products', models.ManyToManyField(default=[], blank=True, to='productdb.Product')),
            ],
            options={
                'ordering': ('product_list_name',),
            },
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('cisco_api_enabled', models.BooleanField(help_text='Indicates the availability of the Cisco API access', default=False)),
                ('cisco_eox_api_auto_sync_enabled', models.BooleanField(help_text='Enable the automatic synchronization of the Cisco EoX API using the configured settings', default=False)),
                ('cisco_eox_api_auto_sync_auto_create_elements', models.BooleanField(help_text='When set to true, received product IDs which are not included in the blacklist are automatically created', default=False)),
                ('cisco_eox_api_auto_sync_queries', models.TextField(help_text='queries that should be executed against the EoX API', default='', blank=True)),
                ('eox_api_blacklist', models.TextField(help_text='comma separated list of elements which should not be created during the API import. It is only relevant if elements are created automatically.', default='', blank=True)),
                ('eox_api_sync_task_id', models.TextField(null=True, default='', blank=True)),
                ('cisco_api_credentials_successful_tested', models.BooleanField(help_text='If credentials are changed in the settings page, it will verify it and write the result to DB', default=False)),
                ('cisco_api_credentials_last_message', models.TextField(help_text='Last (error) message of the Hello API test', default='not tested')),
                ('cisco_eox_api_auto_sync_last_execution_time', models.DateTimeField(help_text='last timestamp when the automatic EoX synchronization was executed', null=True, blank=True)),
                ('cisco_eox_api_auto_sync_last_execution_result', models.TextField(help_text='Last results of the automatic Cisco EoX synchronization', default='not executed')),
                ('demo_mode', models.BooleanField(help_text='If set to true, the application runs in demo mode. Demo mode is used with Testing and will disable all periodic tasks', default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=128, unique=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='product',
            name='lists',
            field=models.ManyToManyField(help_text='associated lists', default=[], blank=True, to='productdb.ProductList'),
        ),
        migrations.AddField(
            model_name='product',
            name='vendor',
            field=models.ForeignKey(help_text='vendor name', on_delete=django.db.models.deletion.SET_DEFAULT, default=0, to='productdb.Vendor'),
        ),
    ]
