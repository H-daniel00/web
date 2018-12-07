# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-12-07 15:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medico', '0002_delete_anestesista'),
    ]

    operations = [
        migrations.AddField(
            model_name='medico',
            name='clave_fiscal',
            field=models.CharField(blank=True, db_column=b'claveFiscal', default=b'', max_length=200, verbose_name=b'Clave Fiscal'),
        ),
        migrations.AddField(
            model_name='medico',
            name='domicilio',
            field=models.CharField(blank=True, db_column=b'direccionMedico', max_length=200, verbose_name=b'Domicilio'),
        ),
        migrations.AddField(
            model_name='medico',
            name='localidad',
            field=models.CharField(blank=True, db_column=b'localidadMedico', max_length=200, verbose_name=b'Localidad'),
        ),
        migrations.AddField(
            model_name='medico',
            name='mail',
            field=models.CharField(blank=True, db_column=b'mail', max_length=200, verbose_name=b'Mail'),
        ),
        migrations.AddField(
            model_name='medico',
            name='matricula',
            field=models.CharField(blank=True, db_column=b'nroMatricula', max_length=200, verbose_name=b'Matr\xc3\xadcula'),
        ),
        migrations.AddField(
            model_name='medico',
            name='responsabilidad_fiscal',
            field=models.CharField(choices=[(b'INSCRIPTO', b'INSCRIPTO'), (b'MONOTRIBUTO', b'MONOTRIBUTO')], db_column=b'responsabilidadFiscal', default=b'MONOTRIBUTO', max_length=200, verbose_name='Responsabilidad Fiscal'),
        ),
        migrations.AddField(
            model_name='medico',
            name='telefono',
            field=models.CharField(blank=True, db_column=b'telMedico', max_length=200, verbose_name=b'Tel\xc3\xa9fono'),
        ),
    ]
