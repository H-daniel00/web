from rest_framework import serializers
from rest_framework.serializers import ValidationError
from django.contrib.admin.models import ADDITION
from django.contrib.auth.models import User

from estudio.models import Estudio
from medico.models import Medico
from .models import MovimientoCaja, TipoMovimientoCaja, MontoAcumulado, ID_GENERAL
from practica.serializers import PracticaSerializer
from obra_social.serializers import ObraSocialSerializer
from paciente.serializers import PacienteSerializer
from medico.serializers import MedicoSerializer
from common.utils import add_log_entry, standar_to_internal_value

from decimal import Decimal

class TipoMovimientoCajaSerializer(serializers.ModelSerializer):

    class Meta:
        model = TipoMovimientoCaja
        fields = ('id', 'descripcion')


class MovimientoCajaSerializer(serializers.ModelSerializer):
    tipo = TipoMovimientoCajaSerializer()

    class Meta:
        model = MovimientoCaja
        fields = ('id', 'concepto', 'monto', 'fecha', 'hora', 'tipo')


class EstudioCajaSerializer(serializers.ModelSerializer):
    practica = PracticaSerializer()
    obra_social = ObraSocialSerializer()
    paciente = PacienteSerializer()
    medico = MedicoSerializer()

    class Meta:
        model = Estudio
        fields = ('id', 'fecha', 'practica', 'obra_social', 'paciente', 'medico')


class MovimientoCajaFullSerializer(serializers.ModelSerializer):
    tipo = TipoMovimientoCajaSerializer()
    estudio = EstudioCajaSerializer()
    medico = MedicoSerializer()
    user = serializers.SerializerMethodField()
    hora = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoCaja
        fields = ('id', 'concepto', 'estudio', 'monto', 'monto_acumulado', 'fecha', 'hora', 'tipo', 'medico', 'user', 'hora')
    
    def get_user(self, obj):
        return str(obj.user) if obj.user else ''
    
    def get_hora(self, obj):
        return str(obj.hora)[:5]

class MovimientoCajaCamposVariablesSerializer(serializers.Serializer):
    tipo_id = serializers.IntegerField(required=True)
    medico_id = serializers.IntegerField(required=False)
    concepto = serializers.CharField(required=False) 
    monto = serializers.DecimalField(16, 2, required=True)

    def to_internal_value(self, data):
        datos = {}
        datos['tipo_id'] = data['tipo_id']
        datos['medico_id'] = data['medico_id']
        datos['monto'] = data['monto']
        datos['concepto'] = data['concepto']

        return standar_to_internal_value(self, datos)

    def validate_medico_id(self, value):
        try:
            if value:
                value = Medico.objects.get(pk=value)
            else:
                value = None
        except Medico.DoesNotExist:
            raise ValidationError('Medico seleccionado no existe')
        return value

    def validate_monto(self, value):
        if not value:
            raise ValidationError('No existe monto')
        try:
            value = Decimal(value)
        except Decimal.InvalidOperation:
            raise ValidationError('El monto no es un numero')
        return value

    def validate_tipo_id(self, value):
        if not value:
            raise ValidationError("El tipo de movimiento es obligatorio")
        try:
            value = TipoMovimientoCaja.objects.get(pk=value)
        except TipoMovimientoCaja.DoesNotExist:
            raise ValidationError('Tipo de movimiento invalido')
        return value

class MovimientoCajaCreateSerializer(serializers.ModelSerializer):
    estudio_id = serializers.IntegerField(required=False)
    movimientos = MovimientoCajaCamposVariablesSerializer(many=True)
    username = serializers.CharField(required=True) 

    class Meta:
        model = MovimientoCaja
        fields = ('estudio_id', 'movimientos', 'username')

    def to_internal_value(self, data):
        datos = {}
        datos['estudio_id'] = data['estudio_id']
        datos['username'] = data['username']
        datos['movimientos'] = [MovimientoCajaCamposVariablesSerializer(data=movimiento) for movimiento in data['movimientos']]

        return standar_to_internal_value(self, datos)

    def validate_username(self, value):
        try:
            value = User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValidationError('Usuario invalido')
        return value

    def validate_movimientos(self, value):
        return [movimiento.validated_data for movimiento in value if movimiento.is_valid(raise_exception=True)]

    def validate_estudio_id(self, value):
        try:
            if value:
                value = Estudio.objects.get(pk=value)
            else:
                value = None
        except Estudio.DoesNotExist:
            raise ValidationError('El estudio seleccionado no existe')
        return value  

    def create(self, validated_data):
        monto_acumulado = MovimientoCaja.objects.last().monto_acumulado

        user = validated_data['username']
        estudio = validated_data['estudio_id']
        movimientos = []

        for movimiento in validated_data['movimientos']:
            tipo = movimiento['tipo_id']
            medico = movimiento['medico_id']
            concepto = movimiento['concepto']
            monto = movimiento['monto']
            monto_acumulado += monto
            movimiento = MovimientoCaja.objects.create(estudio = estudio, user = user, tipo = tipo,
            medico = medico, monto = monto, concepto = concepto, monto_acumulado = monto_acumulado)

            tipo_monto_acumulado = MontoAcumulado.objects.filter(tipo=tipo).first() or MontoAcumulado.objects.get(tipo__id=ID_GENERAL)
            tipo_monto_acumulado.monto_acumulado += monto
            tipo_monto_acumulado.save()

            add_log_entry(movimiento, user, ADDITION, 'CREA')
            movimientos += [movimiento]

        return movimientos

class MovimientoCajaImprimirSerializer(serializers.ModelSerializer):
    hora = serializers.SerializerMethodField()
    usuario = serializers.SerializerMethodField()
    tipo = serializers.SerializerMethodField()
    paciente = serializers.SerializerMethodField()
    obra_social = serializers.SerializerMethodField()
    medico = serializers.SerializerMethodField()
    practica = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoCaja
        fields = ('hora', 'usuario', 'tipo', 'paciente', 'obra_social',
                  'medico', 'practica', 'concepto', 'monto', 'monto_acumulado')

    def get_hora(self, obj):
        return str(obj.hora)[:5] or ''

    def get_tipo(self, obj):
        return str(obj.tipo) or ''

    def get_usuario(self, obj):
        return str(obj.user) if obj.user else ''

    def get_paciente(self, obj):
        return str(obj.estudio.paciente) if obj.estudio else ''

    def get_obra_social(self, obj):
        return str(obj.estudio.obra_social) if obj.estudio else ''

    def get_medico(self, obj):
        medico = obj.medico or (obj.estudio and obj.estudio.medico)
        return str(medico) if medico else ''

    def get_practica(self, obj):
        return str(obj.estudio.practica) if obj.estudio else ''
