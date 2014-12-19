# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('medico', '0001_initial'),
        ('paciente', '0001_initial'),
        ('practica', '0001_initial'),
        ('obra_social', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetalleEstudio',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'nroEstudio')),
                ('idFacturacion', models.IntegerField()),
                ('nroDeOrden', models.CharField(max_length=200)),
                ('idAnestesista', models.IntegerField()),
                ('esPagoContraFactura', models.IntegerField()),
                ('medico', models.ForeignKey(related_name='medico_actuante', db_column=b'idMedicoActuante', to='medico.Medico')),
                ('medicoSolicitante', models.ForeignKey(related_name='medico_solicitante', db_column=b'idMedicoSolicitante', to='medico.Medico')),
                ('obraSocial', models.ForeignKey(to='obra_social.ObraSocial', db_column=b'idObraSocial')),
            ],
            options={
                'db_table': 'cedirData"."tblDetalleEstudio',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Estudio',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'nroEstudio')),
                ('fechaEstudio', models.CharField(max_length=100)),
                ('motivoEstudio', models.CharField(max_length=300)),
                ('informe', models.TextField()),
                ('paciente', models.ForeignKey(to='paciente.Paciente', db_column=b'idPaciente')),
                ('practica', models.ForeignKey(to='practica.Practica', db_column=b'idEstudio')),
            ],
            options={
                'db_table': 'cedirData"."tblEstudios',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PagoCobroEstudio',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'nroEstudio')),
                ('fechaCobro', models.CharField(max_length=100, null=True)),
                ('importeEstudio', models.FloatField()),
                ('importeMedicacion', models.FloatField()),
                ('pagoContraFactura', models.FloatField()),
                ('diferenciaPaciente', models.FloatField()),
                ('pension', models.FloatField()),
                ('importePagoMedico', models.FloatField()),
                ('importePagoMedicoSol', models.FloatField()),
                ('importeCobradoPension', models.FloatField()),
                ('importeCobradoArancelAnestesia', models.FloatField()),
                ('importeEstudioCobrado', models.FloatField()),
                ('importeMedicacionCobrado', models.FloatField()),
                ('arancelAnestesia', models.FloatField()),
            ],
            options={
                'db_table': 'cedirData"."tblPagoCobroEstudio',
            },
            bases=(models.Model,),
        ),
    ]