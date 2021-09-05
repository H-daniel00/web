from datetime import date
from decimal import Decimal
from presentacion.models import Presentacion

from rest_framework import serializers
from rest_framework.serializers import Serializer, ValidationError

from estudio.models import Estudio
from comprobante.models import ID_GRAVADO_EXENTO, ID_GRAVADO_INSCRIPTO_10_5, ID_GRAVADO_INSCRIPTO_21
from comprobante.serializers import GravadoSerializer
from paciente.serializers import PacienteSerializer
from obra_social.serializers import ObraSocialSerializer
from practica.serializers import PracticaSerializer

from .models import Medico, PagoMedico
from .calculo_honorarios.calculador import CalculadorHonorariosPagoMedico
from .calculo_honorarios.porcentajes import Porcentajes

class MedicoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Medico
        fields = ('id', 'nombre', 'apellido', 'matricula')


class PagoMedicoSerializer(serializers.ModelSerializer):

    medico = MedicoSerializer()

    class Meta:
        model = PagoMedico
        fields = ('id', 'fecha', 'medico', 'observacion')


class ListNuevoPagoMedicoSerializer(serializers.ModelSerializer):
    """
    Serializa una lista de estudios para un nuevo pago medico.
    """
    paciente = PacienteSerializer()
    obra_social = ObraSocialSerializer()
    medico_actuante = MedicoSerializer(source='medico')
    medico_solicitante = MedicoSerializer()
    practica = PracticaSerializer()
    importe_neto = serializers.SerializerMethodField()
    retencion_cedir = serializers.SerializerMethodField()
    porcentaje_medico = serializers.SerializerMethodField()
    gastos_administrativos = serializers.SerializerMethodField()
    pago = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    importe_iva = serializers.SerializerMethodField()
    gravado_id = serializers.SerializerMethodField()

    class Meta:
        model = Estudio
        fields = ('id', 'fecha', 'importe_estudio', 'importe_neto', 'fecha_cobro', 'paciente', 'obra_social', 'medico_actuante',
                  'medico_solicitante', 'practica', 'retencion_cedir', 'porcentaje_medico', 'gastos_administrativos',
                  'pago_contra_factura', 'pago', 'importe_iva', 'gravado_id', 'total')

    def get_importe_neto(self, estudio: Estudio) -> Decimal: # Es la plata - gasto administrativo y descuentos por tipo de estudio
        calculador : CalculadorHonorariosPagoMedico = self.context.get('calculador')
        # este es el neto?
        return calculador.get_importe() - calculador.cedir

    def get_retencion_cedir(self, estudio: Estudio) -> Decimal: # Es la plata que se queda el cedir
        calculador : CalculadorHonorariosPagoMedico = self.context.get('calculador')
        return calculador.cedir

    def get_porcentaje_medico(self, estudio: Estudio) -> Decimal:
        # El porcentaje del medico que devuelve aca esta 'partido en 3'
        # Es decir, el 100% es el importe, cuando el 100% deberia ser el neto
        # al mostrar. Habria que transformarlo al porcentaje del neto.
        # Actualmente: importe: 500. cedir: 20%. actuante: 70% solicitante: 10%
        # Como deberia estar:
        # importe: 500. cedir: 20%. neto: 400 actuante: 87.5% solicitante: 12.5%
        calculador : CalculadorHonorariosPagoMedico = self.context.get('calculador')
        medico: Medico = self.context.get('medico')
        porcentaje = Decimal('0')

        if estudio.es_actuante(medico):
            porcentaje += calculador.porcentajes.actuante
        else:
            porcentaje += calculador.porcentajes.solicitante
        
        return porcentaje


    def get_gastos_administrativos(self, estudio: Estudio) -> Decimal:
        calculador : CalculadorHonorariosPagoMedico = self.context.get('calculador')
        return calculador.porcentaje_GA()

    def get_pago(self, estudio: Estudio) -> Decimal:
        # El importe que se le pagara al medico antes de aplicar el iva
        calculador : CalculadorHonorariosPagoMedico = self.context.get('calculador')
        medico: Medico = self.context.get('medico')

        if estudio.es_actuante_y_solicitante(medico):
            return calculador.honorarios_medicos
        elif estudio.es_actuante(medico):
            return calculador.actuante
        else:
            return calculador.solicitante

    def get_total(self, estudio: Estudio) -> Decimal:
        # El importe que se le pagara al medico (con iva)
        return self.get_pago(estudio) + self.get_importe_iva(estudio)

    def get_importe_iva(self, estudio: Estudio) -> Decimal:
        # El importe del iva de cada estudio
        correspondiente = self.get_pago(estudio)
        # tendria que ser gravado.porcentaje
        if estudio.presentacion.comprobante.gravado.id == ID_GRAVADO_INSCRIPTO_21:
            return correspondiente * Decimal(0.21)
        elif estudio.presentacion.comprobante.gravado.id == ID_GRAVADO_INSCRIPTO_10_5:
            return correspondiente * Decimal(0.105)
        elif estudio.presentacion.comprobante.gravado.id == ID_GRAVADO_EXENTO:
            return Decimal(0)
        else:
            # El día que la AFIP apruebe un IVA nuevo esto va a saltar.
            raise NotImplementedError

    def get_gravado_id(self, estudio: Estudio) -> int:
        return estudio.presentacion.comprobante.gravado.id


class CreateNuevoPagoMedicoSerializer(serializers.ModelSerializer):
    """
    {
        "medico": 11,
        "observacion": "asd",
        "lineas": [{"estudio_id": 22, "importe": 22.22}, ...]
    }

    """
    medico = serializers.IntegerField()
    lineas = serializers.ListField()
    observacion = serializers.CharField()


    def to_representation(self, instance):
        return {
            'id': instance.id,
            'medico': instance.medico_id,
            'observacion': instance.observacion,
            'fecha': instance.fecha
        }

    def validate(self, data):
        try:
            medico = Medico.objects.get(pk=data['medico'])
        except Medico.DoesNotExist:
            raise ValidationError(f"El medico {data['medico']} no existe")

        data['observacion'] = data.get('observacion', '')

        for l in data['lineas']:
            estudio : Estudio = Estudio.objects.get(pk=l['estudio_id'])
            importe : Decimal = Decimal(l['importe'])
            if estudio.presentacion.estado != Presentacion.COBRADO:
                raise ValidationError(f"El estudio {l['estudio_id']} aun no fue cobrado")
            if estudio.medico == medico:
                if estudio.pago_medico_actuante is not None:
                    raise ValidationError(f"El estudio {l['estudio_id']} ya esta pago para este actuante.")
                data['es_actuante'] = True
            elif estudio.medico_solicitante == medico:
                if estudio.pago_medico_solicitante  is not None:
                    #TODO: revisar si puede estar pago como actuante pero impago como solicitante
                    raise ValidationError(f"El estudio {l['estudio_id']} ya esta pago para este solicitante.")
                data['es_actuante'] = False
            else:
                raise ValidationError(f"El medico no es actuante ni solicitante del estudio {l['estudio_id']}.")
            if importe == 0:
                raise ValidationError("El importe del pago del estudio no puede ser 0.")

        return data

    def create(self, validated_data) -> PagoMedico:
        medico = Medico.objects.get(pk=validated_data['medico'])
        pago = PagoMedico.objects.create(
            fecha=date.today(),
            medico=medico,
            observacion=validated_data['observacion'],
        )
        for l in validated_data['lineas']:
            estudio : Estudio = Estudio.objects.get(pk=l['estudio_id'])
            importe : Decimal = Decimal(l['importe'])
            if validated_data['es_actuante']:
                estudio.pago_medico_actuante = pago
                estudio.importe_pago_medico = importe
            else:
                # TODO: verificar que pasa si es actuante y solicitante al mismo tiempo
                estudio.pago_medico_solicitante = pago
                estudio.importe_pago_medico_solicitante = importe
            estudio.save()
        return pago

    class Meta:
        model = PagoMedico
        fields = (
            'medico',
            'lineas',
            'observacion'
        )

class GETLineaPagoMedicoSerializer(serializers.ModelSerializer):
    paciente = PacienteSerializer()
    obra_social = ObraSocialSerializer()
    medico_actuante = MedicoSerializer(source='medico')
    medico_solicitante = MedicoSerializer()
    practica = PracticaSerializer()

    class Meta:
        model = Estudio
        fields = ('fecha', 'paciente', 'obra_social', 'medico_actuante', 'medico_solicitante', 'practica',
                  'importe_pago_medico', 'importe_pago_medico_solicitante', 'pago_medico_actuante', 'pago_medico_solicitante', )
