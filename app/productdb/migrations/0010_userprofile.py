# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def save_users(apps, schema_editor):
    User = apps.get_model("auth", "User")
    for u in User.objects.all():
        u.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('productdb', '0009_auto_20160718_0958'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferred_vendor', models.ForeignKey(default=1, help_text='vendor that is selected by default in all vendor specific views', on_delete=django.db.models.deletion.SET_DEFAULT, to='productdb.Vendor', verbose_name='preferred vendor')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(save_users),
    ]
