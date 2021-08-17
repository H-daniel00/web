# pylint: disable=no-name-in-module, import-error
from typing import Dict
from datetime import date
from distutils.util import strtobool
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework.serializers import ValidationError
from rest_framework.decorators import detail_route
from rest_framework.filters import BaseFilterBackend, OrderingFilter
from common.drf.views import StandardResultsSetPagination

from presentacion.models import Presentacion
from presentacion.serializers import PresentacionCreateSerializer, \
    PresentacionRetrieveSerializer, PresentacionSerializer, PresentacionUpdateSerializer, \
    PresentacionRefacturarSerializer, PagoPresentacionParcialSerializer, PresentacionImprimirSerializer
from presentacion.obra_social_custom_code.osde_presentacion_digital import \
    OsdeRowEstudio, OsdeRowMedicacion, OsdeRowPension, OsdeRowMaterialEspecifico
from presentacion.obra_social_custom_code.amr_presentacion_digital import AmrRowEstudio
from presentacion.imprimir_presentacion import generar_pdf_presentacion
from estudio.models import Estudio, ID_SUCURSAL_CEDIR
from estudio.serializers import EstudioDePresentacionRetrieveSerializer
from comprobante.serializers import crear_comprobante_serializer_factory

class PresentacionComprobantesFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        tipo_comprobante = request.query_params.get('tipoComprobante')
        numero_comprobante = request.query_params.get('numeroComprobante')

        if tipo_comprobante:
            queryset = queryset.filter(comprobante__tipo_comprobante__id=tipo_comprobante)

        if numero_comprobante:
            queryset = queryset.filter(comprobante__numero=numero_comprobante)
        return queryset

class PresentacionFieldsFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        anio = (request.query_params.get('anio'))
        obra_social_id = request.query_params.get('obraSocial')
        esta_cobrada = request.query_params.get('presentacionesCobradas', '')
        tipo_presentacion = request.query_params.get('tipoPresentacion')

        if anio:
            queryset = queryset.filter(fecha__year=anio)
        
        if obra_social_id:
            queryset = queryset.filter(obra_social__id=obra_social_id)
        
        if esta_cobrada:
            if strtobool(esta_cobrada) :
                queryset = queryset.filter(estado=Presentacion.COBRADO)
            else:
                queryset = queryset.exclude(estado=Presentacion.COBRADO)
        
        if tipo_presentacion:
            if tipo_presentacion == 'Directa':
                queryset = queryset.filter(obra_social__se_presenta_por_AMR='0')
            else:
                queryset = queryset.filter(obra_social__se_presenta_por_AMR='1')   
        return queryset

class PresentacionSucursalFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        sucursal = request.query_params.get('sucursal')
        if sucursal:
            queryset = queryset.filter(sucursal=sucursal)
        else:
            queryset = queryset.filter(sucursal=ID_SUCURSAL_CEDIR)
        return queryset

class PresentacionViewSet(viewsets.ModelViewSet):
    queryset = Presentacion.objects.all().order_by('-fecha')
    serializer_class = PresentacionSerializer
    filter_backends = (
        PresentacionSucursalFilterBackend,
        PresentacionFieldsFilterBackend,
        PresentacionComprobantesFilterBackend,
        OrderingFilter
    )
    ordering_fields = (
        'id', 'fecha', 'obra_social', 'sucursal',
        'comprobante', 'estado', 'periodo', 'iva',
        'total_cobrado', 'total_facturado', 'comprobante__numero'
    )

    pagination_class = StandardResultsSetPagination
    page_size = 50

    serializers = {
        'retrieve': PresentacionRetrieveSerializer,
        'create': PresentacionCreateSerializer,
        'update': PresentacionUpdateSerializer,
        'partial_update': PresentacionUpdateSerializer,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializer_class)

    @detail_route(methods=['get'])
    def get_detalle_osde(self, request, pk=None):

        presentacion = Presentacion.objects.get(pk=pk)

        csv_string = ''
        estudios = presentacion.estudios.all()

        try:
            for estudio in estudios:
                csv_string = '{}\n{}'.format(csv_string, OsdeRowEstudio(estudio).get_row_osde())

                if estudio.get_total_medicacion_tipo_medicamentos():
                    csv_string = '{}\n{}'.format(csv_string, OsdeRowMedicacion(estudio).get_row_osde())
                if estudio.pension:
                    csv_string = '{}\n{}'.format(csv_string, OsdeRowPension(estudio).get_row_osde())
                for material_esp in estudio.estudioXmedicamento.filter(medicamento__tipo='Mat Esp'):
                    csv_string = '{}\n{}'.format(csv_string, OsdeRowMaterialEspecifico(estudio, material_esp).get_row_osde())

            return HttpResponse(csv_string, content_type='text/plain')
        except Exception as ex:
            response_dict = {'error': str(ex)}
            return JsonResponse(response_dict, status=500)

    @detail_route(methods=['get'])
    def get_detalle_amr(self, request, pk=None):
        presentacion = Presentacion.objects.get(pk=pk)
        csv_string = ''
        estudios = presentacion.estudios.all().order_by('fecha', 'id')
        try:
            comprobante = presentacion.comprobante

            for estudio in estudios:
                csv_string = '{}{}\n'.format(csv_string, AmrRowEstudio(estudio, comprobante).get_row())

            return HttpResponse(csv_string[:-1], content_type='text/plain')
        except Exception as ex:
            response_dict = {'error': str(ex)}
            return JsonResponse(response_dict, status=500)

    @detail_route(methods=['get'])
    def estudios(self, request, pk=None):
        presentacion = Presentacion.objects.get(pk=pk)
        sucursal = request
        estudios = presentacion.estudios.all().order_by('fecha', 'id')
        try:
            response = JsonResponse(EstudioDePresentacionRetrieveSerializer(estudios, many=True).data, safe=False)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=500)
        return response

    @detail_route(methods=['patch'])
    def cerrar(self, request, pk=None):
        # Validar que esta ABIERTO.
        # Pasar a PENDIENTE.
        # Generar comprobante.
        try:
            presentacion = Presentacion.objects.get(pk=pk)
            if presentacion.estado != Presentacion.ABIERTO:
                raise ValidationError("La presentacion debe estar en estado ABIERTO")
            obra_social = presentacion.obra_social
            comprobante_data = request.data
            comprobante_data["neto"] = presentacion.total_facturado
            comprobante_data["nombre_cliente"] = obra_social.nombre
            comprobante_data["domicilio_cliente"] = obra_social.direccion
            comprobante_data["nro_cuit"] = obra_social.nro_cuit.replace('-', '')
            comprobante_data["condicion_fiscal"] = obra_social.condicion_fiscal
            comprobante_data["concepto"] = "FACTURACION CORRESPONDIENTE A " + presentacion.periodo
            comprobante_data["fecha_emision"] = presentacion.fecha
            comprobante_data["fecha_recepcion"] = presentacion.fecha # Para que no explote el azul
            comprobante_serializer = crear_comprobante_serializer_factory(data=comprobante_data)
            comprobante_serializer.is_valid(raise_exception=True)
            comprobante = comprobante_serializer.save()
            linea = comprobante.lineas.first()
            presentacion.estado = Presentacion.PENDIENTE
            presentacion.comprobante = comprobante
            presentacion.iva = linea.iva
            presentacion.save()
            response = JsonResponse(PresentacionSerializer(presentacion).data, safe=False)

        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=400)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=500)
        return response

    @detail_route(methods=['patch'])
    def abrir(self, request, pk=None):
        # Validar que esta PENDIENTE
        # Pasar a ABIERTA.
        # Anular comprobante y generar una nota
        try:
            presentacion = Presentacion.objects.get(pk=pk)
            if presentacion.estado != Presentacion.PENDIENTE:
                return JsonResponse({'error': "La presentacion debe estar en estado PENDIENTE"}, status=400)
            presentacion.comprobante.anular()
            presentacion.comprobante = None
            presentacion.estado = Presentacion.ABIERTO
            presentacion.save()
            return JsonResponse(PresentacionSerializer(presentacion).data, safe=False)
        except Exception as ex:
            return JsonResponse({'error': str(ex)}, status=500)

    @detail_route(methods=['patch'])
    def cobrar(self, request, pk=None):
        # Verificar que esta PENDIENTE
        # Pasar a COBRADA
        # Setear valores cobrados de estudios, total de presentacion
        # Armar un PagoPresentacion
        try:
            pago_data = request.data
            pago_data['presentacion_id'] = pk
            pago_data['fecha'] = date.today()
            pago_data['importe'] = pago_data.get('importe', 0)
            pago_serializer = PagoPresentacionParcialSerializer(data=pago_data)
            pago_serializer.is_valid(raise_exception=True)
            pago = pago_serializer.save()
            diferencia_facturada = pago.presentacion.total_facturado - pago.importe
            response = JsonResponse({"diferencia_facturada": diferencia_facturada})
        except Presentacion.DoesNotExist:
                response = JsonResponse({'error': "No existe una presentacion con esa id"}, status=400)
        except Estudio.DoesNotExist:
                response = JsonResponse({'error': "No existe un estudio con esa id"}, status=400)
        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=400)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=500)
        return response

    @detail_route(methods=['get'])
    def imprimir_presentacion(self, request, pk=None):
        presentacion : Presentacion = Presentacion.objects.get(pk=pk)
        presentacion_serializer = PresentacionImprimirSerializer(presentacion).data
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename="Presentacion_{presentacion.id}.pdf"'
        return generar_pdf_presentacion(response, presentacion_serializer)
    
    @detail_route(methods=['patch'])
    def refacturar_estudios(self, request, pk=None):
        try:
            presentacion = Presentacion.objects.get(pk=pk)
            estudios: Dict = request.data
            presentacion_serializer = PresentacionRefacturarSerializer(presentacion, data=estudios)
            presentacion_serializer.is_valid(raise_exception=True)
            presentacion = presentacion_serializer.save()
            response = JsonResponse({}, status=status.HTTP_200_OK)
        except Presentacion.DoesNotExist:
            response = JsonResponse({'error': 'No existe la presentacion que se quiere modificar'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            response = JsonResponse({'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response
