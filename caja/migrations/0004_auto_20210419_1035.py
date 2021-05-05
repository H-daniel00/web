# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-04-19 10:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('caja', '0003_auto_20200825_0815'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientocaja',
            name='user',
            field=models.ForeignKey(blank=True, db_column='username', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='movimientocaja',
            name='fecha',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='movimientocaja',
            name='hora',
            field=models.TimeField(auto_now_add=True),
        ),
    ]