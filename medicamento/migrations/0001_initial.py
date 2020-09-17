# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-29 16:04


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Medicamento',
            fields=[
                ('id', models.AutoField(db_column='idMedicamento', primary_key=True, serialize=False)),
                ('descripcion', models.CharField(blank=True, db_column='descripcionMedicamento', max_length=300)),
                ('importe', models.DecimalField(db_column='importeMedicamento', decimal_places=2, default='0.00', max_digits=16)),
                ('stock', models.PositiveSmallIntegerField()),
                ('tipo', models.CharField(choices=[('Mat Esp','Material Especifico'), ('Medicaci\xf3n','Medicaci\xc3\xb3n')], default='Medicaci\xf3n', max_length=100)),
                ('codigo_osde', models.CharField(blank=True, db_column='codigoMedicoOSDE', default='', max_length=100)),
            ],
            options={
                'db_table': 'tblMedicamentos',
            },
        ),
        migrations.CreateModel(
            name='Movimiento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('cantidad', models.IntegerField()),
                ('descripcion', models.CharField(max_length=300)),
                ('medicamento', models.ForeignKey(db_column='idMedicamento', on_delete=django.db.models.deletion.CASCADE, to='medicamento.Medicamento')),
            ],
            options={
                'db_table': 'tblMovimientosDeMedicamentos',
            },
        ),
    ]
