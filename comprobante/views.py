# -*- coding: utf-8
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import list_route
from decimal import Decimal

import zipfile
import io

from .imprimir import generar_factura, obtener_comprobante, obtener_filename
from .informe_ventas import obtener_comprobantes_ventas, obtener_archivo_ventas

from comprobante.serializers import ComprobanteListadoSerializer, ComprobanteSerializer, ComprobanteSmallSerializer, CrearComprobanteSerializer
from comprobante.models import Comprobante
from comprobante.calculador_informe import calculador_informe_factory
from comprobante.comprobante_asociado import crear_comprobante_asociado, TipoComprobanteAsociadoNoValidoException
from comprobante.afip import AfipErrorRed, AfipErrorValidacion

from common.drf.views import StandardResultsSetPagination

def imprimir(request, cae):
    # Imprime leyenda?
    leyenda = request.method == 'GET' and 'leyenda' in request.GET

    # Adquiere datos
    comp = obtener_comprobante(cae)

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="{0}.pdf"'.format(obtener_filename(comp['responsable'], comp['cabecera']))

    return generar_factura(response, comp, leyenda)


def ventas(request, responsable : str, anio : str, mes : str) -> HttpResponse:
    if not request.user.is_authenticated or not request.user.has_perm('comprobante.informe_ventas'):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    # Adquiere datos
    comprobantes = obtener_comprobantes_ventas(responsable, anio, mes)

    # Genera el archivo
    (ventas, alicuotas) = obtener_archivo_ventas(comprobantes)

    # Abre un BytesIO para guardar el contenido del archivo
    stream = io.BytesIO()

    # Compresor zip
    zipcomp = zipfile.ZipFile(stream, 'w')

    # Agrega los archivos
    zipcomp.writestr('VENTAS.txt', '\r\n'.join(ventas).encode('ascii', 'replace'))
    zipcomp.writestr('ALICUOTAS.txt', '\r\n'.join(alicuotas).encode('ascii', 'replace'))

    # Cierra el archivo y escribe el contenido
    zipcomp.close()

    # Genera el response adecuado
    resp = HttpResponse(stream.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename={0}_{1}_{2}.zip'.format(responsable, anio, mes)

    return resp

class InformeMensualView(generics.ListAPIView):
    serializer_class = ComprobanteListadoSerializer

    def list(self, request):
        comprobantes = Comprobante.objects.all()
        queryset = comprobantes.filter(fecha_emision__month=request.query_params["mes"],
                                       fecha_emision__year=request.query_params["anio"])
        data = [ComprobanteListadoSerializer(q, context={'calculador': calculador_informe_factory(q)}).data
                for q in queryset]
        return Response(data)

class ComprobanteViewSet(viewsets.ModelViewSet):
    serializer_class = ComprobanteSerializer
    page_size = 50
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CrearComprobanteSerializer
        return ComprobanteSerializer

    def get_queryset(self):
        filtro = self.request.GET.get('filtro').upper() if 'filtro' in self.request.GET else ''
        return Comprobante.objects.filter(nombre_cliente__contains=filtro).order_by('-id')

    @list_route(methods=['POST'])
    def crear_comprobante_asociado(self, request, pk=None):
        id_comprobante_asociado = int(request.POST['id-comprobante-asociado'])
        importe = Decimal(request.POST['importe'])
        concepto = request.POST['concepto']

        try:
            comp = crear_comprobante_asociado(id_comprobante_asociado, importe, concepto)
            content = {'data': ComprobanteSmallSerializer(comp).data , 'message': 'Comprobante creado correctamente'}
            return Response(content, status=status.HTTP_201_CREATED)
        except Comprobante.DoesNotExist:
            content = {'data': {}, 'message': 'El comprobante seleccionado no existe en la base de datos.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        except TipoComprobanteAsociadoNoValidoException:
            content =  {'data': {}, 'message': 'No se puede crear un comprobante asociado con el tipo seleccionado.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        except AfipErrorRed as e:
            content = {'data': {}, 'message': 'No se pudo realizar la conexion con Afip, intente mas tarde.\nError: ' + str(e)}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except AfipErrorValidacion as e:
            content = {'data': {}, 'message': 'Afip rechazo el comprobante.\nError: ' + str(e)}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            content = {'data': {}, 'message': 'Ocurrio un error inesperado.\nError: ' + str(e)}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
