# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-07-24 19:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comprobante', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comprobante',
            name='total_cobrado',
            field=models.DecimalField(db_column='totalCobrado', decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='comprobante',
            name='total_facturado',
            field=models.DecimalField(db_column='totalFacturado', decimal_places=2, default=0, max_digits=16),
        ),
        migrations.AlterField(
            model_name='gravado',
            name='porcentaje',
            field=models.DecimalField(db_column='porcentajeGravado', decimal_places=2, max_digits=4),
        ),
        migrations.AlterField(
            model_name='lineadecomprobante',
            name='importe_neto',
            field=models.DecimalField(db_column='importeNeto', decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='lineadecomprobante',
            name='iva',
            field=models.DecimalField(db_column='importeIVA', decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='lineadecomprobante',
            name='sub_total',
            field=models.DecimalField(db_column='subtotal', decimal_places=2, max_digits=16),
        ),
    ]
