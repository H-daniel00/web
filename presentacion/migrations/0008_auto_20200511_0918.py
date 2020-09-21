# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2020-05-11 09:18


from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presentacion', '0007_auto_20200505_1028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentacion',
            name='total_cobrado',
            field=models.DecimalField(db_column='total', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
    ]
