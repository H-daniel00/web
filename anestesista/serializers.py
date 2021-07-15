from rest_framework import serializers
from rest_framework.serializers import ValidationError

from anestesista.models import Anestesista, Complejidad, SIN_ANESTESIA, EDAD_DIFERENCIADO_DESDE, EDAD_DIFERENCIADO_HASTA, EDAD_DIFERENCIADO_MAYOR_QUE
from anestesista.calculador_honorarios.calculador_honorarios import CalculadorHonorariosAnestesista
from estudio.models import Estudio, ID_SUCURSAL_CEDIR, ID_SUCURSAL_HOSPITAL_ITALIANO
from obra_social.serializers import ObraSocialSerializer
from paciente.serializers import PacienteSerializer
from caja.serializers import MovimientoCajaSerializer
from practica.serializers import PracticaSerializer
from comprobante.serializers import ComprobanteSerializer

from decimal import Decimal, ROUND_UP
from datetime import date
from collections import OrderedDict
from itertools import groupby

class AnestesistaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anestesista
        fields = ('id', 'nombre', 'apellido', 'matricula', 'telefono', 'porcentaje_anestesista')

class EstudioSerializer(serializers.HyperlinkedModelSerializer):
    practica = PracticaSerializer()
    
    class Meta:
        model = Estudio
        fields = ('id', 'fecha', 'practica', )

class LineaCommonFieldsSerializer(serializers.Serializer): # revisar
    sub_total = serializers.DecimalField(18, 2, required=True)
    retencion = serializers.DecimalField(18, 2, required=True)
    importe = serializers.DecimalField(18, 2, required=True)
    alicuota_iva = serializers.DecimalField(4, 2, required=True)
    comprobante = ComprobanteSerializer(required=True)

class LineaPagoAnestesistaVMSerializer(serializers.Serializer):
    fecha = serializers.DateField(required=True)    # datos iniciales 
    paciente = PacienteSerializer(required=True)
    obra_social = ObraSocialSerializer(required=True)
    estudios = EstudioSerializer(required=True, many=True)

#         linea.importe_con_iva = 0 # ???? estos datos estaban de forma original pero parecian usarse
#         linea.importe_iva = 0 # ???

    movimientos_caja = MovimientoCajaSerializer(required=True, many=True)
    es_paciente_diferenciado = serializers.BooleanField(required=True)
    formula = serializers.CharField(required=True)  #datos comunes si la linea es ara o no
    formula_valorizada = serializers.CharField(required=True)
    importe_con_iva = serializers.DecimalField(18, 2, required=True)
    importe_iva = serializers.DecimalField(18, 2, required=True)

    linea_ara = LineaCommonFieldsSerializer() # se devuelven solo los datos relevantes si la linea es ara o no
    linea_no_ara = LineaCommonFieldsSerializer()

    def to_internal_value(self, data): # agregar validates
        data['formula'] = '0' # revisar de ponerlo de forma default, sin usar internal value
        data['formula_valorizada'] = '0'
        data['importe_con_iva'] = 0
        data['importe_iva'] = 0
        data['movimientos_caja'] = []
        data['es_paciente_diferenciado'] = (data['anestesista'].id != SIN_ANESTESIA) and (EDAD_DIFERENCIADO_DESDE <= data['paciente'].get_edad() <= EDAD_DIFERENCIADO_HASTA or data['paciente'].get_edad() >= EDAD_DIFERENCIADO_MAYOR_QUE) # usar metho field

        data['linea_ara'] = {}
        data['linea_no_ara'] = {}

        return data

    def create(self, validated_data):
        calculador_honorarios = CalculadorHonorariosAnestesista(validated_data['anestesista'], validated_data['estudios'], validated_data['obra_social'])
        data_common = {'sub_total': 0, 'retencion': 0, 'importe': 0, 'alicuota_iva': 0, 'comprobante': None}
        common_fields = ('sub_total', 'importe', 'alicuota_iva')
        validated_data['paciente'] = PacienteSerializer(validated_data['paciente']).data
        validated_data['obra_social'] = PacienteSerializer(validated_data['obra_social']).data

        try:
            result = calculador_honorarios.calculate()
        except Complejidad.DoesNotExist:
            validated_data['linea_ara'] = data_common
            return validated_data

        validated_data['formula'] = result.get('formula')
        validated_data['formula_valorizada'] = result.get('formula_valorizada')
        validated_data['movimientos_caja'] = result.get('movimientos_caja')

        ara = result.get('ara')
        if ara:
            for field in common_fields:
                data_common[field] = ara.get(field)
            data_common['retencion'] = ara.get('retencion')
            validated_data['linea_ara'] = data_common

        no_ara = result.get('no_ara')
        if no_ara:
            for field in common_fields:
                data_common[field] = no_ara.get(field)
            data_common['comprobante'] = no_ara.get('comprobante')
            data_common['retencion'] = no_ara.get('a_pagar')
            validated_data['linea_no_ara'] = data_common

        return validated_data

class GenerarVistaNuevoPagoSerializer(serializers.Serializer):
    anio = serializers.IntegerField(required=True)
    mes = serializers.IntegerField(required=True)
    id_sucursal = serializers.IntegerField(required=True)
    anestesista = AnestesistaSerializer(required=True) 

#     pago.porcentaje_anestesista = pago.anestesista.porcentaje_anestesista # ??? estos datos estaban de forma original pero parecian usarse

    totales_no_ara = serializers.JSONField()
    totales_ara = serializers.JSONField()
    subtotales_no_ara = serializers.JSONField()
    totales_iva_no_ara = serializers.JSONField()

    lineas_ARA = LineaPagoAnestesistaVMSerializer(many=True)
    lineas_no_ARA = LineaPagoAnestesistaVMSerializer(many=True)

    def to_internal_value(self, data):
        errors = OrderedDict()
        initial_fields = ('anio', 'mes', 'anestesista', 'id_sucursal')

        for field in initial_fields:
            try:
                if (field in data) and type(data[field]) is int:
                    validate_method = getattr(self, 'validate_' + field, None)
                else:
                    raise ValidationError('Error en los datos')
                if validate_method and type:
                    data[field] = validate_method(data[field])
            except ValidationError as e:
                errors[field] = e.detail
            except Exception as e:
                errors[field] = str(e)

        if errors: 
            raise ValidationError(errors)

        estudios = Estudio.objects.filter(
            anestesista=data['anestesista'],
            fecha__year=data['anio'],
            fecha__month=data['mes'],
            sucursal=data['id_sucursal']).order_by('fecha', 'paciente', 'obra_social')

        data['lineas'] = groupby(estudios, lambda estudio: (estudio.fecha, estudio.paciente, estudio.obra_social))
        data['totales_ara'] = {'iva': Decimal(0), 'subtotal': Decimal(0), 'total': Decimal(0)}
        data['totales_no_ara'] = {'iva00': Decimal(0), 'iva105': Decimal(0), 'iva21': Decimal(0)}
        data['subtotales_no_ara'] = {'iva00': Decimal(0), 'iva105': Decimal(0), 'iva21': Decimal(0)}
        data['totales_iva_no_ara'] = {'iva00': Decimal(0), 'iva105': Decimal(0), 'iva21': Decimal(0)}
        data['lineas_ara'] = []
        data['lineas_no_ara'] = []
        return data

    def validate_anestesista(self, value):
        try:
            value = Anestesista.objects.get(pk=value)
        except Anestesista.DoesNotExist:
            raise ValidationError('El anestesista seleccionado no existe')
        return value

    def validate_anio(self, value):
        if not date.today().year >= value:
            raise ValidationError('Año invalido')
        return value

    def validate_mes(self, value):
        if not(12 >= value and value >= 1):
            raise ValidationError('Mes invalido')
        return value

    def validate_id_sucursal(self, value):
        if not value in (ID_SUCURSAL_HOSPITAL_ITALIANO, ID_SUCURSAL_CEDIR):
            raise ValidationError('Sucursal invalida')
        return value

    def create(self, validated_data):

        for (fecha, paciente, obra_social), estudios in validated_data['lineas']:
            data = {'fecha': fecha, 'paciente': paciente, 'obra_social': obra_social,
                    'estudios': list(estudios), 'anestesista': validated_data['anestesista']} # anestesista se pasa solamente para el calculador de honorarios
            linea = LineaPagoAnestesistaVMSerializer(data=data)
            linea.is_valid()
            linea = linea.save()

        # ver de no repetir datos si la linea es ara o no
            if linea['linea_ara']:
                linea_ara = {**linea, **linea['linea_ara']}
                del linea_ara['linea_ara']
                del linea_ara['linea_no_ara']
                del linea_ara['anestesista']

                validated_data['totales_ara']['subtotal'] += linea_ara['retencion']
                validated_data['totales_ara']['iva'] = validated_data['totales_ara']['subtotal'] * linea_ara['alicuota_iva'] / Decimal(100)
                validated_data['totales_ara']['total'] = validated_data['totales_ara']['subtotal'] + validated_data['totales_ara']['iva']

                validated_data['lineas_ara'] += [linea_ara]

            if linea['linea_no_ara']:
                linea_no_ara = {**linea, **linea['linea_no_ara']}
                del linea_no_ara['linea_ara']
                del linea_no_ara['linea_no_ara']
                del linea_no_ara['anestesista']

                iva_key = 'iva{}'.format(linea_no_ara['alicuota_iva']).replace('.', '')  # TODO: warn! el FE esta esperando especificamente 0, 10.5 y 21. De existir otro IVA va a haber que agregarlo en ULI
                validated_data['subtotales_no_ara'][iva_key] += linea_no_ara['retencion']
                validated_data['totales_iva_no_ara'][iva_key] = validated_data['subtotales_no_ara'][iva_key] * linea_no_ara['alicuota_iva'] / Decimal(100)
                validated_data['totales_no_ara'][iva_key] = validated_data['subtotales_no_ara'][iva_key] + validated_data['totales_iva_no_ara'][iva_key]

                validated_data['lineas_no_ara'] += [linea_no_ara]

        for key in validated_data['totales_ara']:
            validated_data['totales_ara'][key] = validated_data['totales_ara'][key].quantize(Decimal('.01'), ROUND_UP)
        for key in validated_data['subtotales_no_ara']:
            validated_data['subtotales_no_ara'][key] = validated_data['subtotales_no_ara'][key].quantize(Decimal('.01'), ROUND_UP)
        for key in validated_data['totales_iva_no_ara']:
            validated_data['totales_iva_no_ara'][key] = validated_data['totales_iva_no_ara'][key].quantize(Decimal('.01'), ROUND_UP)
        for key in validated_data['totales_no_ara']:
            validated_data['totales_no_ara'][key] = validated_data['totales_no_ara'][key].quantize(Decimal('.01'), ROUND_UP)

        del validated_data['lineas']
        validated_data['anestesista'] = AnestesistaSerializer(validated_data['anestesista']).data
        return validated_data
