from rest_framework import serializers
from obra_social.models import ObraSocial


class ObraSocialSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ObraSocial
        fields = ('id', 'nombre', 'nro_cuit', 'direccion', 'condicion_fiscal', )

class ObraSocialPensionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ObraSocial
        fields = ('id', 'nombre', 'valor_aproximado_pension', )
