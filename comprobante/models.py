from datetime import timedelta
from django.db import models

ID_TIPO_COMPROBANTE_FACTURA = 1
ID_TIPO_COMPROBANTE_LIQUIDACION = 2
ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO = 3
ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO = 4
ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA = 5
ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA = 6
ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA = 7

ID_DOCUMENTO_AFIP_TIPO_CUIT = 80
ID_DOCUMENTO_AFIP_TIPO_CUIL = 86
ID_DOCUMENTO_AFIP_TIPO_DNI = 96

ID_GRAVADO_EXENTO = 1
ID_GRAVADO_INSCRIPTO_10_5 = 2
ID_GRAVADO_INSCRIPTO_21 = 3

TIPO_COMPROBANTE_ASOCIADO = {
    ID_TIPO_COMPROBANTE_FACTURA: ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO,
    ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO: ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO,
    ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO: ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO,
    ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA: ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA,
    ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA: ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA,
    ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA: ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA
}

class TipoComprobante(models.Model):
    nombre = models.CharField(max_length=128, db_column='tipoComprobante')

    class Meta:
        db_table = 'tblComprobantesTipo'

    def __str__(self):
        return str(self.nombre)


class Gravado(models.Model):
    descripcion = models.CharField(max_length=128, db_column='descripcionGravado')
    porcentaje = models.DecimalField(db_column='porcentajeGravado', max_digits=4, decimal_places=2)

    class Meta(object):
        db_table = 'tblGravado'


class Comprobante(models.Model):

    ANULADO = 'ANULADO'
    NO_COBRADO = 'NO COBRADO'
    COBRADO = 'COBRADO'

    ESTADOS = (
        (ANULADO, ANULADO),
        (NO_COBRADO, NO_COBRADO),
        (COBRADO, COBRADO),
    )

    nombre_cliente = models.CharField(max_length=128, db_column='nombreCliente')
    domicilio_cliente = models.CharField(max_length=128, db_column='domicilioCliente')
    nro_cuit = models.CharField(max_length=128, db_column='nroCuit')
    gravado_paciente = models.CharField(max_length=128, db_column='gravadoPaciente', null=True)
    condicion_fiscal = models.CharField(max_length=128, db_column='condicionFiscal')
    responsable = models.CharField(max_length=128, )
    sub_tipo = models.CharField(max_length=50, db_column='subTipo')
    estado = models.CharField(max_length=50, choices=ESTADOS)
    numero = models.IntegerField(db_column='nroComprobante', )
    nro_terminal = models.SmallIntegerField(db_column='nroTerminal', default=1)
    total_facturado = models.DecimalField(db_column='totalFacturado', max_digits=16, decimal_places=2, default=0)
    total_cobrado = models.DecimalField(db_column='totalCobrado', max_digits=16, decimal_places=2, null=True)
    fecha_emision = models.DateField(db_column='fechaEmision')
    fecha_recepcion = models.DateField(db_column='fechaRecepcion', null=True)

    tipo_comprobante = models.ForeignKey(TipoComprobante, db_column='idTipoComprobante')
    factura = models.ForeignKey('comprobante.Comprobante', db_column='idFactura', null=True, blank=True)
    gravado = models.ForeignKey(Gravado, db_column='gravado', null=True, blank=True)

    cae = models.CharField(max_length=128, db_column='CAE', null=True, blank=True)
    vencimiento_cae = models.DateField(db_column='vencimientoCAE', blank=True, null=True)

    @property
    def codigo_afip(self):
        conversion = {
            'A': {
                ID_TIPO_COMPROBANTE_FACTURA: 1,
                ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO: 2,
                ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO: 3,
                ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA: 201,
                ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA: 202,
                ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA: 203
            },
            'B': {
                ID_TIPO_COMPROBANTE_FACTURA: 6,
                ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO: 7,
                ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO: 8,
                ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA: 206,
                ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA: 207,
                ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA: 208
            }
        }
        return conversion[self.sub_tipo][self.tipo_comprobante.id]

    @property
    def tipo_id_afip(self):
        if len(self.nro_cuit.replace('-', '')) <= 9:
            return ID_DOCUMENTO_AFIP_TIPO_DNI
        else:
            return ID_DOCUMENTO_AFIP_TIPO_CUIT

    @property
    def nro_id_afip(self):
        return self.nro_cuit.replace('-', '')

    @property
    def importe_excento_afip(self):
        return 0 if self.gravado and self.gravado.porcentaje else self.total_facturado

    @property
    def importe_gravado_afip(self):
        return (self.total_facturado * 100) / (100 + self.gravado.porcentaje) if self.gravado and self.gravado.porcentaje else 0

    @property
    def importe_alicuota_afip(self):
        return (self.total_facturado * self.gravado.porcentaje) / (100 + self.gravado.porcentaje) if self.gravado and self.gravado.porcentaje else 0

    @property
    def codigo_operacion_afip(self):
        return '0' if self.gravado and self.gravado.porcentaje else 'E'

    @property
    def codigo_alicuota_afip(self):
        return (2 + self.gravado.id) if self.gravado else 3

    #TODO obtener el nombre de las obras sociales por alguna consulta a una base de datos
    @property
    def fecha_vencimiento(self):
        dias = 30
        if self.tipo_comprobante.id == ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA and "SWISS MEDICAL" in self.nombre_cliente.upper():
            dias = 60
        if self.tipo_comprobante.id == ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA and "SANCOR" in self.nombre_cliente.upper():
            dias = 80
        return self.fecha_emision + timedelta(days=dias)

    def anular(self):
        from comprobante.comprobante_asociado import crear_comprobante_asociado
        if self.tipo_comprobante.id != ID_TIPO_COMPROBANTE_LIQUIDACION:
            linea = LineaDeComprobante.objects.filter(comprobante=self).first()
            nuevo_comprobante = crear_comprobante_asociado(self.id, linea.importe_neto, "Anula comprobante nro " + str(self.id), TIPO_COMPROBANTE_ASOCIADO[self.tipo_comprobante.id])
        else:
            nuevo_comprobante = None
        self.estado = Comprobante.ANULADO
        self.save()
        return nuevo_comprobante

    class Meta(object):
        permissions = (
            ("informe_ventas", "Permite generar el informe de ventas."),
        )
        db_table = 'tblComprobantes'


class LineaDeComprobante(models.Model):
    comprobante = models.ForeignKey(Comprobante, db_column='idComprobante', related_name='lineas')
    concepto = models.CharField(max_length=1000, )
    sub_total = models.DecimalField(db_column='subtotal', max_digits=16, decimal_places=2)
    iva = models.DecimalField(db_column='importeIVA', max_digits=16, decimal_places=2)
    importe_neto = models.DecimalField(db_column='importeNeto', max_digits=16, decimal_places=2)

    class Meta(object):
        db_table = 'tblComprobanteLineas'
