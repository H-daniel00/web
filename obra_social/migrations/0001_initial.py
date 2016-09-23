# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-23 18:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ObraSocial',
            fields=[
                ('id', models.AutoField(db_column=b'idObraSocial', primary_key=True, serialize=False)),
                ('nombre', models.CharField(db_column=b'obraSocial', max_length=200)),
            ],
            options={
                'ordering': ['nombre'],
                'db_table': 'AlmacenObraSocial',
            },
        ),
    ]
