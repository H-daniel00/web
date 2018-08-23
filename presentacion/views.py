from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from common.drf.views import StandardResultsSetPagination
from presentacion.models import Presentacion
from presentacion.serializers import PresentacionSerializer
from presentacion.obra_social_custom_code.osde_presentacion_digital import \
    OsdeRowEstudio, OsdeRowMedicacion, OsdeRowPension, OsdeRowMaterialEspecifico


class PresentacionViewSet(viewsets.ModelViewSet):
    queryset = Presentacion.objects.all().order_by('-fecha')
    serializer_class = PresentacionSerializer
    filter_fields = ('obra_social',)
    pagination_class = StandardResultsSetPagination
    page_size = 50

    @detail_route(methods=['get'])
    def get_detalle_osde(self, request, pk=None):

        presentacion = Presentacion.objects.get(pk=pk)

        csv_string = ''
        estudios = presentacion.estudios.all()

        for estudio in estudios:
            csv_string = '{}\n{}'.format(csv_string, OsdeRowEstudio(estudio).get_row_osde())

            if estudio.get_total_medicacion():
                csv_string = '{}\n{}'.format(csv_string, OsdeRowMedicacion(estudio).get_row_osde())
            if estudio.pension:
                csv_string = '{}\n{}'.format(csv_string, OsdeRowPension(estudio).get_row_osde())
            for material_esp in estudio.estudioXmedicamento.filter(medicamento__tipo=u'Mat Esp'):
                csv_string = '{}\n{}'.format(csv_string, OsdeRowMaterialEspecifico(estudio, material_esp).get_row_osde())

        response = HttpResponse(csv_string, content_type='text/csv')
        return response
