# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-01 19:41


from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contenidos', '0003_contenidos_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='contenido',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
