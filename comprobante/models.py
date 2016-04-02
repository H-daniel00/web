from django.db import models

class ComprobanteLinea(models.Model):
    id = models.BigIntegerField(primary_key=True)
    concepto = models.TextField(blank=True)
    subtotal = models.FloatField(blank=True, null=True)
    idcomprobante = models.ForeignKey('Comprobante', db_column='idComprobante', related_name='lineas', blank=True, null=True)  # Field name made lowercase.
    importeiva = models.DecimalField(db_column='importeIVA', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    importeneto = models.DecimalField(db_column='importeNeto', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'cedirData\".\"tblComprobanteLineas'


class Comprobante(models.Model):
    id = models.BigIntegerField(primary_key=True)
    nombrecliente = models.TextField(db_column='nombreCliente', blank=True)  # Field name made lowercase.
    domiciliocliente = models.TextField(db_column='domicilioCliente', blank=True)  # Field name made lowercase.
    nrocuit = models.TextField(db_column='nroCuit', blank=True)  # Field name made lowercase.
    condicionfiscal = models.TextField(db_column='condicionFiscal', blank=True)  # Field name made lowercase.
    responsable = models.TextField(blank=True)
    idtipocomprobante = models.ForeignKey('ComprobanteTipo', db_column='idTipoComprobante', blank=True, null=True)  # Field name made lowercase.
    fechaemision = models.DateField(db_column='fechaEmision', blank=True, null=True)  # Field name made lowercase.
    fecharecepcion = models.DateField(db_column='fechaRecepcion', blank=True, null=True)  # Field name made lowercase.
    estado = models.TextField(max_length=-1, blank=True)
    subtipo = models.TextField(db_column='subTipo', blank=True)  # Field name made lowercase.
    idfactura = models.BigIntegerField(db_column='idFactura', blank=True, null=True)  # Field name made lowercase.
    totalfacturado = models.FloatField(db_column='totalFacturado', blank=True, null=True)  # Field name made lowercase.
    totalcobrado = models.FloatField(db_column='totalCobrado', blank=True, null=True)  # Field name made lowercase.
    gravado = models.ForeignKey('Gravado', db_column='gravado', blank=True, null=True)
    nrocomprobante = models.IntegerField(db_column='nroComprobante')  # Field name made lowercase.
    gravadopaciente = models.TextField(db_column='gravadoPaciente', blank=True)  # Field name made lowercase.
    nroterminal = models.IntegerField(db_column='nroTerminal', blank=True, null=True)  # Field name made lowercase.
    cae = models.TextField(db_column='CAE', blank=True)  # Field name made lowercase.
    vencimientoCAE = models.DateField(db_column='vencimientoCAE', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cedirData\".\"tblComprobantes'


class ComprobanteTipo(models.Model):
    id = models.BigIntegerField(primary_key=True)
    tipocomprobante = models.TextField(db_column='tipoComprobante')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'cedirData\".\"tblComprobantesTipo'


class Gravado(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    descripciongravado = models.TextField(db_column='descripcionGravado', blank=True)  # Field name made lowercase.
    porcentajegravado = models.FloatField(db_column='porcentajeGravado', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'cedirData\".\"tblGravado'
