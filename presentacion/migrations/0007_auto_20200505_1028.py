# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2020-05-05 10:28


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('presentacion', '0006_auto_20200504_0106'),
    ]

    operations = [
        migrations.RenameField(
            model_name='presentacion',
            old_name='total',
            new_name='total_cobrado',
        ),
    ]
