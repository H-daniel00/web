# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-08-26 10:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presentacion', '0009_presentacion_saldo_positivo'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentacion',
            name='remito',
            field=models.CharField(default='', max_length=128),
        ),
    ]
