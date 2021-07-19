from decimal import Decimal

from django.db import models
from comprobante.models import Comprobante
from obra_social.models import ObraSocial

ID_SUCURSAL_CEDIR = 1
ID_SUCURSAL_HOSPITAL_ITALIANO = 2

class Presentacion(models.Model):

    PENDIENTE = 0
    COBRADO = 1
    ABIERTO = 2

    ESTADOS = (
        (PENDIENTE, 'Pendiente'),  # 'estado = 0 significa que esta facturado, y no se pueden agregar mas estudios ni modificar nada porque esta cerrado
        (COBRADO, 'Cobrado'),    # 'estado = 1 significa que se facturo y se cobro
        (ABIERTO, 'Abierto'),    # 'estado = 2 la facturacion esta abierta a agregar o modificar estudios
    )

    id = models.AutoField(primary_key=True, db_column='idFacturacion')
    obra_social = models.ForeignKey(ObraSocial, db_column='idObraSocial')
    sucursal = models.IntegerField('Sucursal', default=ID_SUCURSAL_CEDIR, choices=[(ID_SUCURSAL_CEDIR, "Cedir"), (ID_SUCURSAL_HOSPITAL_ITALIANO, "Hospital Italiano")])
    comprobante = models.ForeignKey(Comprobante, db_column='idComprobante', related_name='presentacion', null=True)
    fecha = models.DateField('Fecha', db_column='fechaFacturacion')
    estado = models.SmallIntegerField(db_column='pagado', choices=ESTADOS)
    periodo = models.CharField(max_length=128)
    iva = models.DecimalField(max_digits=16, decimal_places=2)
    total_cobrado = models.DecimalField(db_column='total', max_digits=16, decimal_places=2, default=Decimal('0.00'))
    total_facturado = models.DecimalField(db_column='totalFacturado', max_digits=16, decimal_places=2, default=Decimal('0.00'))
    remito = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        db_table = 'tblFacturacion'

    def __str__(self):
        return '%s %s' % (self.fecha, self.obra_social)


class PagoPresentacion(models.Model):
    id = models.AutoField(primary_key=True, db_column='idPagoFact')
    presentacion = models.ForeignKey(Presentacion, db_column='idFacturacion', related_name='pago')
    fecha = models.DateField('Fecha', db_column='fechaPagoFact')
    nro_recibo = models.CharField(max_length=128, db_column='nroRecivo')
    importe = models.DecimalField(db_column='importePago', max_digits=16, decimal_places=2)
    retencion_impositiva = models.DecimalField(db_column='gastoAdministrativo', default=Decimal('0.00'), max_digits=16, decimal_places=2)

    class Meta:
        db_table = 'tblPagoFacturacion'
