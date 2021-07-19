# pylint: disable=no-self-argument
from django.db import models

from medico.models import Medico
from estudio.models import Estudio
from django.contrib.auth.models import User

ID_GENERAL = 1
ID_HONORARIO_MEDICO = 2
ID_HONORARIO_ANESTESISTA = 3
ID_MEDICACION = 4
ID_PRACTICA = 5
ID_DESCARTABLE = 6
ID_MATERIAL_ESPECIFICO = 7
ID_PAGO_A_MEDICO = 8
ID_CONSULTORIO_1 = 9
ID_COSEGURO = 10
ID_EGRESO = 11
ID_CONSULTORIO_2 = 12
ID_DEPOSITO_REINTEGRO = 13
ID_IVA = 14

def get_monto_acumulado(tipo):
    if tipo in (ID_CONSULTORIO_2, ID_CONSULTORIO_1):
        return MontoAcumulado.objects.get(tipo= tipo)
    return MontoAcumulado.objects.get(tipo=ID_GENERAL)

class TipoMovimientoCaja(models.Model):
    descripcion = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'tblCajaTipoDeMovimientos'

    def __str__(self):
        return str(self.descripcion)

class MovimientoCaja(models.Model):
    concepto = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    tipo = models.ForeignKey(TipoMovimientoCaja, db_column='idTipoDeMovimiento')
    estudio = models.ForeignKey(Estudio, db_column='nroEstudio', related_name='movimientos_caja', blank=True, null=True)
    medico = models.ForeignKey(Medico, db_column='idMedico', blank=True, null=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_acumulado = models.DecimalField(db_column='montoAcumulado', max_digits=14, decimal_places=2)
    user = models.ForeignKey(User, db_column='username', blank=True, null=True)
    estado = models.BooleanField(default=False) #Este campo debe removerse cuando el azul no se utilice mas

    class Meta:
        db_table = 'tblCajaMovimientos'

class MontoAcumulado(models.Model):
    monto_acumulado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tipo = models.ForeignKey(TipoMovimientoCaja)

    class Meta:
        db_table = 'tblMontoAcumulado'
