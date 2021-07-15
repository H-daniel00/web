# -*- coding: utf-8 -*-
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.renderers import JSONRenderer
from rest_framework.serializers import ValidationError

import copy
from decimal import Decimal, ROUND_UP
from itertools import groupby

from estudio.models import Estudio, ID_SUCURSAL_CEDIR
from anestesista.models import Anestesista, PagoAnestesistaVM, LineaPagoAnestesistaVM, Complejidad, SIN_ANESTESIA
from anestesista.serializers import AnestesistaSerializer, GenerarVistaNuevoPagoSerializer
from anestesista.calculador_honorarios.calculador_honorarios import CalculadorHonorariosAnestesista

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def generar_vista_nuevo_pago(request, id_anestesista, anio, mes): # ver de pasarlo al viewset
    try:
        sucursal = request.GET.get('sucursal', ID_SUCURSAL_CEDIR)
        data = {'anio': int(anio), 'mes': int(mes), 'id_sucursal': int(sucursal), 'anestesista': int(id_anestesista)} 
        pago_serializer = GenerarVistaNuevoPagoSerializer(data=data)
        if not pago_serializer.is_valid():
            raise ValidationError(pago_serializer.errors)
        pago = pago_serializer.save()
        print(pago)
        response = JsonResponse(pago, status=status.HTTP_200_OK)

    except ValidationError as ex:
        response = JsonResponse({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:
        response = JsonResponse({'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response

class AnestesistaNombreApellidoFilterBackend(filters.BaseFilterBackend):
    
    """
    Filtro de anestesista por nombre o apellido
    """
    def filter_queryset(self, request, queryset, view):
        search_text = request.query_params.get('search_text')


        if search_text:
            if str.isdigit(search_text):
                queryset = queryset.filter(Q(matricula__icontains=search_text))
            else:
                search_params = [x.strip() for x in search_text.split(',')]
                nomOApe1 = search_params[0]
                nomOApe2 = search_params[1] if len(search_params) >= 2 else ''
                queryset = queryset.filter((Q(nombre__icontains=nomOApe1) & Q(apellido__icontains=nomOApe2)) |
                    (Q(nombre__icontains=nomOApe2) & Q(apellido__icontains=nomOApe1)))
        return queryset

class AnastesistaViewSet(viewsets.ModelViewSet):
    model = Anestesista
    queryset = Anestesista.objects.all()
    serializer_class = AnestesistaSerializer
    filter_backends = (AnestesistaNombreApellidoFilterBackend, )
    pagination_class = None