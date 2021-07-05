from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.core.validators import ValidationError
from rest_framework import filters
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django.contrib.admin.models import ADDITION, CHANGE
from django.core.paginator import Paginator, InvalidPage

from common.drf.views import StandardResultsSetPagination
from common.utils import add_log_entry
from estudio.models import Estudio
from estudio.models import Medicacion
from medicamento.models import Medicamento
from caja.models import MovimientoCaja
from estudio.serializers import EstudioSerializer, EstudioCreateUpdateSerializer, EstudioRetrieveSerializer, EstudioAsociadoConMovimientoSerializer, EstudioImprimirListadoSerializer
from estudio.serializers import MedicacionSerializer, MedicacionCreateUpdateSerializer
from .imprimir import generar_informe
from .imprimir_listado import generar_pdf_estudio_list
from datetime import date
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

def imprimir(request, id_estudio):

    estudio = Estudio.objects.get(pk=id_estudio)

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="Estudio de {0}.pdf"'.format(estudio.paciente.apellido)

    return generar_informe(response, estudio)


def add_default_medicacion(request):

    id_estudio = request.POST['id_estudio']
    default_medicamentos_ids = (2, 3, 4, 5, 6, 7, 8, 22, 23, 35, 36, 37, 42, 48, 109, 128, 144, 167, 169)

    estudio = Estudio.objects.get(pk=id_estudio)
    for medicamento_id in default_medicamentos_ids:
        medicacion = Medicacion()
        medicacion.estudio = estudio
        medicacion.medicamento = Medicamento.objects.get(pk=medicamento_id)
        medicacion.importe = medicacion.medicamento.importe
        medicacion.save()

    response_dict = {
        'status': 200,
        'estudio': estudio.id,
        'message': "default medicacion added"
    }

    return JsonResponse(response_dict)


class EstudioObraSocialFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de estudios por obra social
    """
    def filter_queryset(self, request, queryset, view):
        obra_social = request.query_params.get('obra_social')
        if obra_social:
            queryset = queryset.filter(obra_social__nombre__icontains=obra_social)
        return queryset

class EstudioMedicoFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de estudios por medico actuante
    """
    def filter_queryset(self, request, queryset, view):
        apellido = request.query_params.get('medico_apellido')
        nombre = request.query_params.get('medico_nombre')
        if apellido:
            queryset = queryset.filter(medico__apellido__icontains=apellido)
        if nombre:
            queryset = queryset.filter(medico__nombre__icontains=nombre)
        return queryset


class EstudioMedicoSolicitanteFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de estudios por medico solicitante
    """
    def filter_queryset(self, request, queryset, view):
        apellido = request.query_params.get('medico_solicitante_apellido')
        nombre = request.query_params.get('medico_solicitante_nombre')
        if apellido:
            queryset = queryset.filter(medico_solicitante__apellido__icontains=apellido)
        if nombre:
            queryset = queryset.filter(medico_solicitante__nombre__icontains=nombre)
        return queryset


class EstudioPacienteFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de estudios por paciente
    """
    def filter_queryset(self, request, queryset, view):
        dni = request.query_params.get('paciente_dni')
        apellido = request.query_params.get('paciente_apellido')
        nombre = request.query_params.get('paciente_nombre')
        paciente_id = request.query_params.get('paciente_id')
        if dni:
            queryset = queryset.filter(paciente__dni__icontains=dni)
        if apellido:
            queryset = queryset.filter(paciente__apellido__icontains=apellido)
        if nombre:
            queryset = queryset.filter(paciente__nombre__icontains=nombre)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        return queryset


class EstudioFechaFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de estudios por fecha
    """
    def filter_queryset(self, request, queryset, view):
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        return queryset

class SucursalFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        sucursal = request.query_params.get('sucursal')
        if sucursal:
            queryset = queryset.filter(sucursal=sucursal)

        return queryset

class EstudioPracticaFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        practica = request.query_params.get('practica')
        if practica:
            queryset = queryset.filter(practica__id=practica)
        return queryset

class EstudioViewSet(viewsets.ModelViewSet):
    model = Estudio
    queryset = Estudio.objects.all()
    serializer_class = EstudioSerializer
    filter_backends = (EstudioObraSocialFilterBackend, EstudioMedicoFilterBackend,
        EstudioMedicoSolicitanteFilterBackend, EstudioPacienteFilterBackend,
        EstudioFechaFilterBackend, SucursalFilterBackend, filters.OrderingFilter, EstudioPracticaFilterBackend )
    pagination_class = StandardResultsSetPagination
    ordering_fields = ('fecha', 'id')
    page_size = 20

    serializers = {
        'create': EstudioCreateUpdateSerializer,
        'update': EstudioCreateUpdateSerializer,
        'retrieve': EstudioRetrieveSerializer,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializer_class)

    def perform_create(self, serializer):
        estudio = serializer.save()
        add_log_entry(estudio, self.request.user, ADDITION, 'CREA')

    def perform_update(self, serializer):
        estudio = serializer.save()
        add_log_entry(estudio, self.request.user, CHANGE, 'ACTUALIZA')

    @detail_route(methods=['put'])
    def anular_pago_contra_factura(self, request, pk=None):
        try:
            estudio = Estudio.objects.get(pk=pk)
            if not estudio.es_pago_contra_factura:
                raise ValidationError('No se puede anular un estudio que no fue dado de pago contra factura')
            estudio.anular_pago_contra_factura()
            estudio.save()
            add_log_entry(estudio, self.request.user, CHANGE, 'ANULA PAGO CONTRA FACTURA')
            response = JsonResponse({}, status=status.HTTP_200_OK)
        except ValidationError as e:
            response = JsonResponse({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return response

    @detail_route(methods=['put'])
    def realizar_pago_contra_factura(self, request, pk=None):
        try:
            importe = Decimal(request.data.get('pago_contra_factura'))
            if importe < 0:
                raise ValidationError('No se permiten valores negativos en el campo importe')

            estudio = Estudio.objects.get(pk=pk)
            if estudio.es_pago_contra_factura and importe == estudio.pago_contra_factura:
                raise ValidationError('El importe ingresado debe ser distinto al importe anterior')

            estudio.set_pago_contra_factura(importe)
            estudio.save()
            add_log_entry(estudio, self.request.user, CHANGE, 'PAGO CONTRA FACTURA')
            response = JsonResponse({}, status=status.HTTP_200_OK)
        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)

        return response

    @detail_route(methods=['patch'])
    def update_importes(self, request, pk=None):
        pension = request.data.get('pension')
        diferencia_paciente = request.data.get('diferencia_paciente')
        arancel_anestesia = request.data.get('arancel_anestesia')

        estudio = Estudio.objects.get(pk=pk)
        estudio.pension = Decimal(pension)
        estudio.diferencia_paciente = Decimal(diferencia_paciente)
        estudio.arancel_anestesia = Decimal(arancel_anestesia)

        if estudio.presentacion_id:
            return Response({'success': False, 'message': 'El estudio esta presentado/pcf y no se puede modificar'}, status=status.HTTP_400_BAD_REQUEST)

        estudio.save()
        add_log_entry(estudio, self.request.user, CHANGE, 'ACTUALIZA IMPORTES')
        return Response({'success': True})

    @list_route(methods=['GET'])
    def imprimir_listado(self, request):
        try:
            estudios = self.filter_queryset(self.queryset).order_by('paciente__apellido', 'paciente__nombre')

            if len(estudios) == 0:
                raise ValidationError('Debe seleccionar al menos un estudio para imprimir')

            estudios_serializer = EstudioImprimirListadoSerializer(estudios, many=True).data
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'filename="Listado_de_estudios_generado_{date.today()}.pdf"'

            response = generar_pdf_estudio_list(response, estudios_serializer)
        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return response

    @list_route(methods=['GET'])
    def get_estudios_con_asociados(self, request):
        try:
            estudios = self.filter_queryset(self.queryset)
            paginator = Paginator(estudios, self.pagination_class.page_size)
            page_number = request.GET.get('page', 1)
            estudios = paginator.page(page_number).object_list
            estudios = EstudioAsociadoConMovimientoSerializer(estudios, many = True).data
            response = JsonResponse({'results': estudios, 'count': paginator.count}, status=status.HTTP_200_OK)
        except InvalidPage as ex: # pagina fuera de rango
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response

    def destroy(self, request, pk=None):
        try:
            estudio = Estudio.objects.get(pk = pk)
            if(date.today() - estudio.fecha).days >= 3:
                raise ValidationError('No se puede eliminar estudios con mas de tres dias de ingreso')
            
            if estudio.presentacion_id:
                raise ValidationError('No se puede eliminar estudios que esten en una presentacion')
            
            ct = ContentType.objects.get_for_model(Estudio)
            LogEntry.objects.filter(content_type_id=ct.pk).filter(object_id = estudio.id).delete()
            movimientos_caja_asociados = MovimientoCaja.objects.filter(estudio = estudio)
            for movimiento in movimientos_caja_asociados:
                movimiento.estudio = None
                mensaje = "ESTE MOVIMIENTO POSEÍA UN ESTUDIO ASOCIADO. Paciente: {0}. Fecha: {1}. ".format(estudio.paciente, estudio.fecha)
                movimiento.concepto = mensaje + movimiento.concepto
                movimiento.save()
            medicaciones = Medicacion.objects.filter(estudio = estudio)
            for medicacion in medicaciones:
                medicacion.delete()
            estudio.delete()
            response = JsonResponse({}, status=status.HTTP_200_OK)
        except Estudio.DoesNotExist as e:
            response = JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            response = JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response

class MedicacionEstudioFilterBackend(filters.BaseFilterBackend):
    """
    Filtro de medicaciones por estudio
    """
    def filter_queryset(self, request, queryset, view):
        estudio = request.query_params.get('estudio')
        if estudio:
            queryset = queryset.filter(estudio__id=estudio)
        return queryset


class MedicacionViewSet(viewsets.ModelViewSet):
    model = Medicacion
    queryset = Medicacion.objects.all()
    serializer_class = MedicacionSerializer
    filter_backends = (MedicacionEstudioFilterBackend, )

    serializers = {
        'create': MedicacionCreateUpdateSerializer,
        'update': MedicacionCreateUpdateSerializer,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializer_class)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"estudio": instance.estudio.id})

    def perform_destroy(self, instance):
        instance.delete()

    @list_route(methods=['DELETE'])
    def delete_medicacion(self, request):
        try:
            self.filter_queryset(self.queryset).delete()
            response = JsonResponse({}, status=status.HTTP_200_OK)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response
