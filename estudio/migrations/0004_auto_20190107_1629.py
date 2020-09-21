# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-01-07 16:29


from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estudio', '0003_estudio_anestesista'),
    ]

    operations = [
        migrations.AlterField(
            model_name='estudio',
            name='arancel_anestesia',
            field=models.DecimalField(db_column='arancelAnestesia', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='diferencia_paciente',
            field=models.DecimalField(db_column='diferenciaPaciente', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_cobrado_arancel_anestesia',
            field=models.DecimalField(db_column='importeCobradoArancelAnestesia', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_cobrado_pension',
            field=models.DecimalField(db_column='importeCobradoPension', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_estudio',
            field=models.DecimalField(db_column='importeEstudio', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_estudio_cobrado',
            field=models.DecimalField(db_column='importeEstudioCobrado', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_medicacion',
            field=models.DecimalField(db_column='importeMedicacion', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_medicacion_cobrado',
            field=models.DecimalField(db_column='importeMedicacionCobrado', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_pago_medico',
            field=models.DecimalField(db_column='importePagoMedico', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='importe_pago_medico_solicitante',
            field=models.DecimalField(db_column='importePagoMedicoSol', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='informe',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='motivo',
            field=models.CharField(blank=True, db_column='motivoEstudio', default='', max_length=300, verbose_name='Motivo'),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='pago_contra_factura',
            field=models.DecimalField(db_column='pagoContraFactura', decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='estudio',
            name='pension',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
        migrations.AlterField(
            model_name='medicacion',
            name='importe',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=16),
        ),
    ]
