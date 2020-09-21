# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-29 16:04


from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Sala',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('observaciones', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'turnos_salas',
            },
        ),
    ]
