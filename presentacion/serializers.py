from decimal import Decimal
from datetime import date

from rest_framework import serializers
from rest_framework import status
from rest_framework.serializers import ValidationError
from presentacion.models import PagoPresentacion, Presentacion
from obra_social.models import ObraSocial
from comprobante.models import Comprobante, TipoComprobante, Gravado, LineaDeComprobante, ID_TIPO_COMPROBANTE_LIQUIDACION
from estudio.models import Estudio
from estudio.serializers import EstudioDePresentacionRetrieveSerializer
from obra_social.serializers import ObraSocialSerializer
from comprobante.serializers import ComprobanteSerializer
from estudio.serializers import EstudioDePresentacionImprimirSerializer

class EstadoField(serializers.Field):
    def to_representation(self, value):
        return Presentacion.ESTADOS[value][1]

    def to_internal_value(self, data):
        return [estado for estado in Presentacion.ESTADOS if estado[1] == data][0][0]

class PresentacionSerializer(serializers.ModelSerializer):
    obra_social = ObraSocialSerializer()
    comprobante = ComprobanteSerializer()
    estado = EstadoField()

    class Meta:
        model = Presentacion

class PresentacionRetrieveSerializer(serializers.ModelSerializer):
    obra_social = ObraSocialSerializer()
    comprobante = ComprobanteSerializer()
    estado = EstadoField()
    estudios = EstudioDePresentacionRetrieveSerializer(many=True)

    class Meta:
        model = Presentacion

class PresentacionImprimirSerializer(serializers.ModelSerializer):
    obra_social = ObraSocialSerializer()
    estudios = serializers.SerializerMethodField()
    
    class Meta:
        model = Presentacion
        fields = (
            'obra_social',
            'estudios',
            'periodo',
            'fecha'
        )

    def get_estudios(self, presentacion):
        estudios = Estudio.objects.filter(presentacion=presentacion).order_by('fecha', 'paciente__dni')
        return [EstudioDePresentacionImprimirSerializer(estudio).data for estudio in estudios]

class PresentacionCreateSerializer(serializers.ModelSerializer):
    obra_social_id = serializers.IntegerField()
    estudios = serializers.ListField()

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'obra_social_id': instance.obra_social_id,
            'sucursal': instance.sucursal,
            'periodo': instance.periodo,
            'fecha': instance.fecha,
        }

    def validate(self, data):
        for estudio_data in data['estudios']:
            estudio = Estudio.objects.get(pk=estudio_data['id'])
            if estudio.obra_social_id != data['obra_social_id']:
                raise ValidationError('El estudio id = {0} es de una obra social distinta a la presentacion'.format(estudio.id))
            if estudio.presentacion_id != 0:
                raise ValidationError('El estudio id = {0} ya se encuentra presentado'.format(estudio.id))
            if estudio.sucursal != data['sucursal']:
                raise ValidationError('El estudio id = {0} no es de esta sucursal'.format(estudio.id))
        return data

    def create(self, validated_data):
        estudios_data = validated_data['estudios']
        del validated_data['estudios']
        validated_data['comprobante'] = None
        validated_data['iva'] = 0
        validated_data['estado'] = Presentacion.ABIERTO
        presentacion = Presentacion.objects.create(**validated_data)
        for estudio_data in estudios_data:
            estudio = Estudio.objects.get(pk=estudio_data['id'])
            estudio.presentacion = presentacion
            estudio.nro_de_orden = estudio_data.get("nro_de_orden", estudio.nro_de_orden)
            estudio.importe_estudio = estudio_data.get("importe_estudio", estudio.importe_estudio)
            estudio.pension = estudio_data.get("pension", estudio.pension)
            estudio.diferencia_paciente = estudio_data.get("diferencia_paciente", estudio.diferencia_paciente)
            estudio.importe_medicacion = estudio.get_total_medicacion()
            estudio.arancel_anestesia = estudio_data.get("arancel_anestesia", estudio.arancel_anestesia)
            estudio.save()
        estudios = Estudio.objects.filter(id__in=[e["id"] for e in estudios_data])
        presentacion.total_facturado = sum([e.get_importe_total_facturado() for e in estudios])
        presentacion.save()
        return presentacion

    class Meta:
        model = Presentacion
        fields = (
            'id',
            'obra_social_id',
            'sucursal',
            'periodo',
            'fecha',
            'estudios',
        )

class PresentacionUpdateSerializer(serializers.ModelSerializer):
    estudios = serializers.ListField()

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'obra_social_id': instance.obra_social_id,
            'sucursal': instance.sucursal,
            'periodo': instance.periodo,
            'fecha': instance.fecha,
        }

    def validate(self, data):
        for estudio_data in data['estudios']:
            estudio = Estudio.objects.get(pk=estudio_data['id'])
            if estudio.obra_social_id != self.instance.obra_social_id:
                raise ValidationError('El estudio id = {0} es de una obra social distinta a la presentacion'.format(estudio.id))
            if estudio.presentacion_id != 0 and estudio.presentacion_id != self.instance.id:
                raise ValidationError('El estudio id = {0} ya se encuentra presentado'.format(estudio.id))
            if estudio.sucursal != self.instance.sucursal:
                raise ValidationError('El estudio id = {0} no es de esta sucursal'.format(estudio.id))
        return data

    def update(self, instance, validated_data):
        instance.periodo = validated_data.get("periodo", instance.periodo)
        instance.fecha = validated_data.get("fecha", instance.fecha)
        estudios_data = validated_data['estudios']
        for estudio in instance.estudios.all():
            estudio.presentacion_id = 0
            estudio.save()
        for estudio_data in estudios_data:
            estudio = Estudio.objects.get(pk=estudio_data['id'])
            estudio.presentacion = instance
            estudio.nro_de_orden = estudio_data.get("nro_de_orden", estudio.nro_de_orden)
            estudio.importe_estudio = estudio_data.get("importe_estudio", estudio.importe_estudio)
            estudio.pension = estudio_data.get("pension", estudio.pension)
            estudio.diferencia_paciente = estudio_data.get("diferencia_paciente", estudio.diferencia_paciente)
            estudio.importe_medicacion = estudio.get_total_medicacion()
            estudio.arancel_anestesia = estudio_data.get("arancel_anestesia", estudio.arancel_anestesia)
            estudio.save()
        estudios = Estudio.objects.filter(id__in=[e["id"] for e in estudios_data])
        instance.total_facturado = sum([e.get_importe_total_facturado() for e in estudios])
        instance.save()
        return instance
    class Meta:
        model = Presentacion
        fields = (
            'id',
            'periodo',
            'fecha',
            'estudios',
        )

class PresentacionRefacturarSerializer(serializers.ModelSerializer):
    estudios = serializers.ListField()

    class Meta:
        model = Presentacion
        fields = (
            'estudios',
        )
    
    def validate(self, data):
        for estudio_data in data['estudios']:
            estudio = Estudio.objects.get(pk=estudio_data)
            if estudio.obra_social_id != self.instance.obra_social_id:
                raise ValidationError('El estudio id = {0} es de una obra social distinta a la presentacion'.format(estudio.id))
            if estudio.presentacion_id != 0 and estudio.presentacion_id != self.instance.id:
                raise ValidationError('El estudio id = {0} ya se encuentra presentado'.format(estudio.id))
            if estudio.sucursal != self.instance.sucursal:
                raise ValidationError('El estudio id = {0} no es de esta sucursal'.format(estudio.id))

        if self.instance.estado != Presentacion.PENDIENTE:
            raise ValidationError('La presentacion debe estar en estado PENDIENTE')
        
        return data
    
    def update(self, instance, validated_data):
        estudios_data = validated_data['estudios']
        for estudio_id in estudios_data:
            estudio = Estudio.objects.get(pk=estudio_id)
            estudio.presentacion_id = 0
            estudio.save()
        return instance

class PagoPresentacionSerializer(serializers.ModelSerializer):
    presentacion_id = serializers.IntegerField()
    estudios = serializers.ListField()
    class Meta:
        model = PagoPresentacion
        fields = (
            'presentacion_id',
            'estudios',
            'fecha',
            'retencion_impositiva',
            'nro_recibo',
        )

    def validate_presentacion_id(self, value):
        presentacion = Presentacion.objects.get(pk=value)
        if presentacion.estado != Presentacion.PENDIENTE:
            raise ValidationError("La presentacion debe estar en estado PENDIENTE")
        return value

    def validate_estudios(self, value):
        presentacion = Presentacion.objects.get(pk=self.initial_data['presentacion_id'])
        estudios_data = value
        if len(estudios_data) < presentacion.estudios.count():
            raise ValidationError("Faltan datos de estudios")
        required_props = ['id', 'importe_cobrado_pension',
                'importe_cobrado_arancel_anestesia', 'importe_estudio_cobrado', 'importe_medicacion_cobrado']
        for e in estudios_data:
            if not all([prop in list(e.keys()) for prop in required_props]):
                raise ValidationError("Cada estudio debe tener los campos 'id', \
                    'importe_cobrado_pension', 'importe_cobrado_arancel_anestesia', \
                    'importe_estudio_cobrado', 'importe_medicacion_cobrado'")
            estudio = Estudio.objects.get(pk=e['id'])
            if estudio.presentacion != presentacion:
                raise ValidationError("El estudio {0} no corresponde a esta presentacion".format(e['id']))
        return value

    def create(self, validated_data):
        presentacion = Presentacion.objects.get(pk=validated_data['presentacion_id'])
        estudios_data = validated_data['estudios']
        for e in estudios_data:
            estudio = Estudio.objects.get(pk=e['id'])
            if estudio.presentacion != presentacion:
                raise ValidationError("El estudio {0} no corresponde a esta presentacion".format(e['id']))
            estudio.importe_estudio_cobrado = e['importe_estudio_cobrado']
            estudio.importe_medicacion_cobrado = e['importe_medicacion_cobrado']
            estudio.importe_cobrado_pension = e['importe_cobrado_pension']
            estudio.importe_cobrado_arancel_anestesia = e['importe_cobrado_arancel_anestesia']
            estudio.fecha_cobro = date.today()
            estudio.save()
        total = sum([
            e.importe_cobrado_pension
            + e.importe_cobrado_arancel_anestesia
            + e.importe_estudio_cobrado
            + e.importe_medicacion_cobrado
            for e in presentacion.estudios.all()])
        presentacion.total_cobrado = total
        presentacion.estado = Presentacion.COBRADO
        presentacion.comprobante.estado = Comprobante.COBRADO
        presentacion.comprobante.total_cobrado = total
        presentacion.comprobante.save()
        presentacion.save()
        return PagoPresentacion.objects.create(
            presentacion_id=validated_data['presentacion_id'],
            fecha=validated_data['fecha'],
            nro_recibo=validated_data['nro_recibo'],
            importe=total,
            retencion_impositiva=validated_data['retencion_impositiva'],
        )