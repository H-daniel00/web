# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-01-07 16:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paciente', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paciente',
            name='dni',
            field=models.IntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='domicilio',
            field=models.CharField(blank=True, db_column='direccion', max_length=200, verbose_name='Domicilio'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='edad',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='email',
            field=models.CharField(blank=True, db_column='e_mail', max_length=200, null=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='nroAfiliado',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nro Afiliado'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='sexo',
            field=models.CharField(choices=[(b'Masculino', b'Masculino'), (b'Femenino', b'Femenino')], max_length=50),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='telefono',
            field=models.CharField(blank=True, db_column='tel', max_length=200, verbose_name='Telefono'),
        ),
    ]
