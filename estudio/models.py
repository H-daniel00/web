# -*- coding: utf-8
import datetime
from decimal import Decimal, ROUND_UP

from django.db import models
from django.db.models.signals import pre_save

from common.utils import generate_uuid
from medico.models import Medico, PagoMedico
from anestesista.models import Anestesista
from practica.models import Practica
from obra_social.models import ObraSocial
from paciente.models import Paciente
from medicamento.models import Medicamento
from presentacion.models import Presentacion


MAX_DAYS_VIDEO_LINK_AVAILABLE = 30

ID_SUCURSAL_CEDIR = 1
ID_SUCURSAL_HOSPITAL_ITALIANO = 2

class Estudio(models.Model):

    PENDIENTE = 0
    COBRADO = 1
    NO_COBRADO = 2

    ESTADOS = (
        'PENDIENTE', # Se colocan en este orden para prevalecer el orden de presentacion
        'COBRADO',
        'NO COBRADO',
    )

    id = models.AutoField(primary_key=True, db_column="nroEstudio")
    paciente = models.ForeignKey(Paciente, db_column="idPaciente")
    fecha = models.DateField('Fecha', db_column="fechaEstudio")
    practica = models.ForeignKey(Practica, db_column="idEstudio")
    motivo = models.CharField('Motivo', db_column="motivoEstudio", max_length=300, blank=True, default='')
    informe = models.TextField(blank=True, default='')
    enlace_video = models.CharField(max_length=256, db_column="enlaceVideo", blank=True)
    public_id = models.CharField(max_length=35, db_column="publicID", default=generate_uuid)
    sucursal = models.IntegerField('Sucursal', db_column='sucursal', default=ID_SUCURSAL_CEDIR, choices=[(ID_SUCURSAL_CEDIR, "Cedir"), (ID_SUCURSAL_HOSPITAL_ITALIANO, "Hospital Italiano")])

    medico = models.ForeignKey(Medico, db_column="idMedicoActuante", related_name='medico_actuante')
    obra_social = models.ForeignKey(ObraSocial, db_column="idObraSocial")
    medico_solicitante = models.ForeignKey(Medico, db_column="idMedicoSolicitante", related_name='medico_solicitante')
    presentacion = models.ForeignKey(Presentacion, db_column='idFacturacion', null=True, blank=True, related_name='estudios')
    nro_de_orden = models.CharField(db_column='nroDeOrden', max_length=200)
    anestesista = models.ForeignKey(Anestesista, db_column="idAnestesista", related_name='anestesista')

    es_pago_contra_factura = models.IntegerField(db_column="esPagoContraFactura", default=0)
    medicacion = models.ManyToManyField(Medicamento, through='Medicacion')

    fecha_cobro = models.CharField(db_column="fechaCobro", null=True, max_length=100)
    importe_estudio = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="importeEstudio")
    importe_medicacion = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="importeMedicacion")
    pago_contra_factura = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="pagoContraFactura")
    # TODO: ver donde se setea esta diferencia_paciente y si hay comprobantes o que
    diferencia_paciente = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="diferenciaPaciente")
    pension = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    importe_pago_medico = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column='importePagoMedico')
    importe_pago_medico_solicitante = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column='importePagoMedicoSol')
    #diferencia_paciente_medicacion = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column=u'diferenciaPacienteMedicacion')
    pago_medico_actuante = models.ForeignKey(PagoMedico, db_column='nroPagoMedicoAct', null=True, blank=True, related_name='estudios_actuantes')
    pago_medico_solicitante = models.ForeignKey(PagoMedico, db_column='nroPagoMedicoSol', null=True, blank=True, related_name='estudios_solicitantes')
    importe_cobrado_pension = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="importeCobradoPension")
    importe_cobrado_arancel_anestesia = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="importeCobradoArancelAnestesia")
    importe_estudio_cobrado = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="importeEstudioCobrado")
    importe_medicacion_cobrado = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="importeMedicacionCobrado")
    arancel_anestesia = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), db_column="arancelAnestesia")

    class Meta:
        db_table = 'tblEstudios'
        ordering = ['id']

    def __str__(self):
        return '%s %s' % (self.fecha, self.paciente)

    @property
    def fecha_vencimiento_link_video(self):
        return self.fecha + datetime.timedelta(days=MAX_DAYS_VIDEO_LINK_AVAILABLE)

    def is_link_vencido(self):
        return True if datetime.date.today() >= self.fecha_vencimiento_link_video else False

    def save(self, *args, **kwargs):
        if not self.id:  # creation
            self.set_create_defaults()
        super(Estudio, self).save(*args, **kwargs)

    def set_create_defaults(self):
        # TODO: move this to database default values on each field
        # self.motivo = u''
        # self.informe = u''
        self.nro_de_orden = ''
        # self.anestesista_id = 1
        self.es_pago_contra_factura = 0
        self.fecha_cobro = None
        self.importe_estudio = 0
        self.importe_medicacion = 0
        self.pago_contra_factura = 0
        self.diferencia_paciente = 0
        self.pension = 0
        self.importe_pago_medico = 0
        self.importe_pago_medico_solicitante = 0
        self.pago_medico_actuante = None
        self.pago_medico_solicitante = None
        self.importe_cobrado_pension = 0
        self.importe_cobrado_arancel_anestesia = 0
        self.importe_estudio_cobrado = 0
        self.importe_medicacion_cobrado = 0
        self.arancel_anestesia = 0

    @property
    def retencion_impositiva(self):
        """
        Para calculo de honorarios e informe de comprobantes.
        """
        if self.obra_social.se_presenta_por_AMR == "1" or self.obra_social.se_presenta_por_AMR == 1:
            return Decimal("0.32")
        else:
            return Decimal("0.25")

    def es_actuante(self, medico):
        return self.medico == medico

    def es_solicitante(self, medico):
        return self.medico_solicitante == medico

    def es_actuante_y_solicitante(self, medico):
        return self.es_actuante(medico) and self.es_solicitante(medico)

    def get_importe_total_facturado(self):
        return Decimal(self.importe_estudio).quantize(Decimal('.01'), ROUND_UP) - \
               Decimal(self.diferencia_paciente).quantize(Decimal('.01'), ROUND_UP) + \
               Decimal(self.arancel_anestesia).quantize(Decimal('.01'), ROUND_UP) + \
               Decimal(self.pension).quantize(Decimal('.01'), ROUND_UP) + \
               Decimal(self.importe_medicacion).quantize(Decimal('.01'), ROUND_UP)

    def get_total_medicacion_tipo_medicamentos(self):
        """
        Return: total medicacion sin material especifico
        """
        total_medicacion = 0
        for medicacion in self.estudioXmedicamento.filter(medicamento__tipo='Medicación'):
            total_medicacion += medicacion.importe

        return Decimal(total_medicacion).quantize(Decimal('.01'), ROUND_UP)

    def get_total_medicacion_tipo_material_especifico(self):
        total = sum([medicacion.importe for medicacion in self.estudioXmedicamento.filter(medicamento__tipo='Mat Esp')])
        return Decimal(total).quantize(Decimal('.01'), ROUND_UP)

    def get_total_medicacion(self):
        total = sum([medicacion.importe for medicacion in self.estudioXmedicamento.all()])
        return Decimal(total).quantize(Decimal('.01'), ROUND_UP)

    def set_pago_contra_factura(self, importe):
        assert not self.presentacion_id, 'Estudio ya fue presentado y no puede modificarse'
        assert not(self.pago_medico_actuante_id or self.pago_medico_solicitante_id), 'Estudio ya fue pagado al medico y no puede modificarse'

        self.es_pago_contra_factura = 1
        self.pago_contra_factura = importe
        self.fecha_cobro = datetime.datetime.today()

    def anular_pago_contra_factura(self):
        assert bool(self.es_pago_contra_factura), 'El estudio no esta como Pago Contra Factura'
        assert not(self.pago_medico_actuante_id or self.pago_medico_solicitante_id), 'Estudio ya fue pagado al medico y no puede modificarse'
        assert self.fecha_cobro, 'El estudio no esta cobrado y por ende no es Pago Contra Factura'

        self.es_pago_contra_factura = 0
        self.pago_contra_factura = 0
        self.fecha_cobro = None


def asignar_presentacion_nula(sender, instance, **kwargs):
    """
    Esto es un hook para asignar una presentacion nula cuando se crea un estudio.
    Esto es porque por defecto el campo idFacturacion = 0 cuando deberia ser igual a None.
    Cuando se actualice esto, este codigo puede ser eliminado.
    """
    if instance.id:
        return  # si no esta creando, no hay nada que hacer

    presentacion = Presentacion()
    presentacion.id = 0
    instance.presentacion = presentacion

pre_save.connect(asignar_presentacion_nula, sender=Estudio, dispatch_uid="asignar_presentacion_nula")


class Medicacion(models.Model):
    id = models.AutoField(primary_key=True, db_column="idMedicacion")
    medicamento = models.ForeignKey(Medicamento, db_column="idMedicamento")
    estudio = models.ForeignKey(Estudio, db_column="nroEstudio", related_name='estudioXmedicamento')
    importe = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'tblMedicacion'
