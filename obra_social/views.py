from django.http import JsonResponse
from rest_framework import filters, viewsets
from rest_framework.decorators import detail_route
from rest_framework.serializers import ValidationError

from estudio.models import Estudio, ID_SUCURSAL_CEDIR
from estudio.serializers import EstudioSinPresentarSerializer
from obra_social.models import ObraSocial
from obra_social.serializers import ObraSocialSerializer

class ObraSocialNombreFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de obra social por nombre
    """
    def filter_queryset(self, request, queryset, view):
        nombre = request.query_params.get('nombre')
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)

        return queryset

# Create your views here.
class ObraSocialViewSet(viewsets.ModelViewSet):
    model = ObraSocial
    queryset = ObraSocial.objects.all()
    serializer_class = ObraSocialSerializer
    filter_backends = (ObraSocialNombreFilterBackend, )
    pagination_class = None

    @detail_route(methods=['get'])
    def estudios_sin_presentar(self, request, pk=None):
        # Un estudio no presentado en realidad deberia tener presentacion=NULL
        # El legacy le pone id=0
        # Como aca presentacion es FK (como corresponde), esto esta bastante DUDOSO por ahora y complica despues el serializer
        # Cuando el legacy arregle eso (o lo tiremos) esto deberia cambiar para buscar presentacion=None
        try:
            sucursal = request.query_params.get('sucursal', default=ID_SUCURSAL_CEDIR)
            estudios = Estudio.objects.filter(
                obra_social__pk=pk,
                es_pago_contra_factura=0,
                presentacion_id=0,
                fecha__year__gt=2017,
                sucursal=sucursal,
            ).order_by('fecha', 'id')
            datos = { 
                'estudios': EstudioSinPresentarSerializer(estudios, many=True).data,
                'observaciones': ObraSocial.objects.get(pk=pk).observaciones
            }
            response = JsonResponse(datos, status=200, safe=False)
        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=400)
        except ObraSocial.DoesNotExist as ex:
            response = JsonResponse({'error': 'Obra social invalida'}, status=400)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=500)
        return response
