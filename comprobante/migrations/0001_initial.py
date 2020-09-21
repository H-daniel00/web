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
            name='Comprobante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_cliente', models.CharField(db_column='nombreCliente', max_length=128)),
                ('domicilio_cliente', models.CharField(db_column='domicilioCliente', max_length=128)),
                ('nro_cuit', models.CharField(db_column='nroCuit', max_length=128)),
                ('gravado_paciente', models.CharField(db_column='gravadoPaciente', max_length=128)),
                ('condicion_fiscal', models.CharField(db_column='condicionFiscal', max_length=128)),
                ('responsable', models.CharField(max_length=128)),
                ('sub_tipo', models.CharField(db_column='subTipo', max_length=50)),
                ('estado', models.CharField(choices=[('ANULADO', 'ANULADO'), ('NO COBRADO', 'NO COBRADO'), ('COBRADO', 'COBRADO')], max_length=50)),
                ('numero', models.IntegerField(db_column='nroComprobante')),
                ('nro_terminal', models.SmallIntegerField(db_column='nroTerminal', default=1)),
                ('total_facturado', models.FloatField(db_column='totalFacturado', default=0)),
                ('total_cobrado', models.FloatField(db_column='totalCobrado')),
                ('fecha_emision', models.DateField(db_column='fechaEmision')),
                ('fecha_recepcion', models.DateField(db_column='fechaRecepcion')),
                ('cae', models.CharField(blank=True, db_column='CAE', max_length=128, null=True)),
                ('vencimiento_cae', models.DateField(blank=True, db_column='vencimientoCAE', null=True)),
                ('factura', models.ForeignKey(blank=True, db_column='idFactura', null=True, on_delete=django.db.models.deletion.CASCADE, to='comprobante.Comprobante')),
            ],
            options={
                'db_table': 'tblComprobantes',
                'permissions': (('informe_ventas', 'Permite generar el informe de ventas.'),),
            },
        ),
        migrations.CreateModel(
            name='Gravado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(db_column='descripcionGravado', max_length=128)),
                ('porcentaje', models.FloatField(db_column='porcentajeGravado')),
            ],
            options={
                'db_table': 'tblGravado',
            },
        ),
        migrations.CreateModel(
            name='LineaDeComprobante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concepto', models.CharField(max_length=128)),
                ('sub_total', models.FloatField(db_column='subtotal')),
                ('iva', models.FloatField(db_column='importeIVA')),
                ('importe_neto', models.FloatField(db_column='importeNeto')),
                ('comprobante', models.ForeignKey(db_column='idComprobante', on_delete=django.db.models.deletion.CASCADE, related_name='lineas', to='comprobante.Comprobante')),
            ],
            options={
                'db_table': 'tblComprobanteLineas',
            },
        ),
        migrations.CreateModel(
            name='TipoComprobante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(db_column='tipoComprobante', max_length=128)),
            ],
            options={
                'db_table': 'tblComprobantesTipo',
            },
        ),
        migrations.AddField(
            model_name='comprobante',
            name='gravado',
            field=models.ForeignKey(blank=True, db_column='gravado', null=True, on_delete=django.db.models.deletion.CASCADE, to='comprobante.Gravado'),
        ),
        migrations.AddField(
            model_name='comprobante',
            name='tipo_comprobante',
            field=models.ForeignKey(db_column='idTipoComprobante', on_delete=django.db.models.deletion.CASCADE, to='comprobante.TipoComprobante'),
        ),
    ]
