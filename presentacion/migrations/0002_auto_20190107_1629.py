# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-01-07 16:29
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('presentacion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentacion',
            name='comprobante',
            field=models.ForeignKey(db_column='idComprobante', on_delete=django.db.models.deletion.CASCADE, related_name='presentacion', to='comprobante.Comprobante'),
        ),
        migrations.AlterField(
            model_name='presentacion',
            name='iva',
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='presentacion',
            name='total',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='presentacion',
            name='total_facturado',
            field=models.DecimalField(db_column='totalFacturado', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
    ]