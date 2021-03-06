from decimal import Decimal, ROUND_UP
from datetime import date

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from presentacion.models import PagoPresentacion, Presentacion
from comprobante.models import Comprobante
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
    fecha_cobro = serializers.SerializerMethodField()
    nro_recibo = serializers.SerializerMethodField()

    class Meta:
        model = Presentacion

    def get_fecha_cobro(self, obj):
        if(obj.estado == Presentacion.COBRADO):
            return PagoPresentacion.objects.get(presentacion=obj).fecha
        return None

    def get_nro_recibo(self, obj):
        if(obj.estado == Presentacion.COBRADO):
            return PagoPresentacion.objects.get(presentacion=obj).nro_recibo
        return None

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

    class Meta:
        model = Presentacion
        fields = (
            'id',
            'periodo',
            'fecha',
            'estudios',
            'remito',
        )

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'obra_social_id': instance.obra_social_id,
            'sucursal': instance.sucursal,
            'periodo': instance.periodo,
            'estado': instance.estado,
            'remito': instance.remito,
            'fecha': instance.fecha,
        }

    def validate(self, data):
        if self.instance.estado == Presentacion.COBRADO:
            raise ValidationError('Las presentaciones cobradas no pueden actualizarse')

        if 'remito' in data and not data['remito'].isnumeric():
            raise ValidationError('El numero de remito debe ser numerico')

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

        if instance.estado == Presentacion.ABIERTO:
            estudios = Estudio.objects.filter(id__in=[e["id"] for e in estudios_data])
            instance.total_facturado = sum([e.get_importe_total_facturado() for e in estudios])
            instance.periodo = validated_data.get("periodo", instance.periodo)
            instance.fecha = validated_data.get("fecha", instance.fecha)
        else:
            instance.remito = validated_data.get('remito', instance.remito)

        instance.save()
        return instance

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

    def update_estudios(self, estudios_data, presentacion, presentacion_id, fecha_cobro = None):
        for e in estudios_data:
            estudio = Estudio.objects.get(pk=e['id'])

            if estudio.presentacion.id != presentacion_id:
                raise ValidationError("El estudio {0} no corresponde a esta presentacion".format(e['id']))

            estudio.importe_estudio_cobrado = e['importe_estudio_cobrado']
            estudio.importe_medicacion_cobrado = e['importe_medicacion_cobrado']
            estudio.importe_cobrado_pension = e['importe_cobrado_pension']
            estudio.importe_cobrado_arancel_anestesia = e['importe_cobrado_arancel_anestesia']
            estudio.fecha_cobro = fecha_cobro
            estudio.save()

    def create(self, validated_data):
        presentacion = Presentacion.objects.get(pk=validated_data['presentacion_id'])
        self.update_estudios(validated_data['estudios'], presentacion, presentacion.id, date.today())
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

class PagoPresentacionParcialSerializer(PagoPresentacionSerializer):
    estudios_impagos = serializers.ListField()
    importe = serializers.DecimalField(16, 2)
    remito = serializers.CharField(allow_blank=True)

    class Meta:
        model = PagoPresentacion
        fields = (
            'presentacion_id', 'estudios', 'estudios_impagos', 'fecha',
            'retencion_impositiva', 'nro_recibo', 'importe', 'remito'
        )

    def validate_remito(self, value):
        if value and not value.isnumeric():
            raise ValidationError('El numero de remito debe ser numerico')
        return value

    def validate_presentacion_id(self, value):
        presentacion = Presentacion.objects.get(pk=value)
        if presentacion.estado != Presentacion.PENDIENTE:
            raise ValidationError("La presentacion debe estar en estado PENDIENTE")
        return value

    def validate_estudios(self, value):
        presentacion = Presentacion.objects.get(pk=self.initial_data['presentacion_id'])
        estudios_data = value
        if not estudios_data:
            raise ValidationError("Debe pagarse al menos un estudio")
        if len(estudios_data) + len(self.initial_data['estudios_impagos']) < presentacion.estudios.count():
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

    def validate_importe(self, importe):
        if importe == 0:
            return importe

        importe_total = sum([Decimal(e['importe_estudio_cobrado'])
            + Decimal(e['importe_medicacion_cobrado'])
            + Decimal(e['importe_cobrado_pension'])
            + Decimal(e['importe_cobrado_arancel_anestesia'])
            for e in self.initial_data['estudios']])

        saldo = Presentacion.objects.get(pk=self.initial_data['presentacion_id']).saldo_positivo
        importe_cobrado = importe + saldo

        if importe_cobrado < importe_total:
            raise ValidationError('El importe ingresado no es suficiente para pagar los estudios seleccionados')

        return importe_cobrado - importe_total

    def create(self, validated_data):
        # Traemos la presentacion
        presentacion_id = validated_data['presentacion_id']
        presentacion = Presentacion.objects.get(pk=presentacion_id)
        presentacion.saldo_positivo = Decimal(0)
        presentacion.remito = validated_data['remito']
        presentacion.save()

        # Si hay estudios impagos los agregamos a una nueva presentacion
        if validated_data['estudios_impagos']:
            # Creamos la nueva presentacion
            presentacion.id = None
            presentacion.saldo_positivo = validated_data['importe'] # Ya que validate_importe devuelve el saldo
            presentacion.save()

            for estudio in validated_data['estudios_impagos']:
                Estudio.objects.filter(id=estudio['id']).update(presentacion=presentacion)

            presentacion_serializer = PresentacionUpdateSerializer(presentacion, data={
                'estudios': validated_data['estudios_impagos'],
            }, partial=True)
            presentacion_serializer.is_valid(raise_exception=True)
            presentacion_serializer.save()

        # Pagamos la presentacion anterior
        del validated_data['estudios_impagos']
        presentacion_serializer = PagoPresentacionSerializer(data=validated_data)
        presentacion_serializer.is_valid(raise_exception=True)
        return presentacion_serializer.save()
