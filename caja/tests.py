# pylint: disable=no-name-in-module, import-error
import json
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from rest_framework import status

from distutils.util import strtobool

from caja.models import MovimientoCaja

class ListadoCajaTest(TestCase):
    fixtures = ['caja.json', 'medicos.json', 'pacientes.json', 'medicos.json', 'practicas.json', 'obras_sociales.json',
        'anestesistas.json', 'presentaciones.json', 'comprobantes.json', 'estudios.json', 'medicamentos.json']

    def setUp(self):
        self.user = User.objects.create_user(username='walter', password='xx11', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='walter', password='xx11')

    def test_listado(self):
        response = self.client.get('/api/caja/', {})
        results = json.loads(response.content).get('results')
        self.assertEqual(len(results), MovimientoCaja.objects.all().count())

    def test_filtro_concepto_funciona(self):
        keywords = 'ingreso X'
        response = self.client.get(f'/api/caja/?concepto={keywords}')
        
        assert response.status_code == status.HTTP_200_OK
        
        results = json.loads(response.content).get('results')
        for movimiento in results:
            for word in keywords.split():
                assert word in movimiento['concepto']

    def test_filtro_medico_funciona(self):
        parametro_busqueda = '1'
        response = self.client.get('/api/caja/?medico={0}'.format(parametro_busqueda))
        results = json.loads(response.content).get('results')
    
        for result in results:
            assert result['medico']['id'] == int(parametro_busqueda)

        assert MovimientoCaja.objects.count() - MovimientoCaja.objects.exclude(medico__id=parametro_busqueda).count() == len(results)

    def test_filtro_fecha_funciona(self):
        fecha_inicial = '2019-02-01'
        fecha_final = '2019-02-08'
        response = self.client.get('/api/caja/?fecha_desde={0}&fecha_hasta={1}'.format(fecha_inicial, fecha_final))
        results = json.loads(response.content).get('results')

        for result in results:
            fecha = list(map(int, result['fecha'].split('-')))
            assert fecha[0] == 2019
            assert fecha[1] == 2
            assert 1 <= fecha[2] <= 8

    def test_filtro_tipo_movimiento_funciona(self):
        parametro_busqueda = 'General'
        response = self.client.get('/api/caja/?tipo_movimiento={0}'.format(parametro_busqueda))
        results = json.loads(response.content).get('results')

        for result in results:
            assert parametro_busqueda == result['tipo']['descripcion']

        assert MovimientoCaja.objects.count() - MovimientoCaja.objects.exclude(tipo__descripcion=parametro_busqueda).count() == len(results)

    def test_filtro_estudio_funciona(self):
        parametro_busqueda = 'True'
        response = self.client.get('/api/caja/?incluir_estudio={0}'.format(parametro_busqueda))
        results = json.loads(response.content).get('results')

        for result in results:
            assert result['estudio'] is not None

        assert MovimientoCaja.objects.count() - MovimientoCaja.objects.filter(estudio__isnull=strtobool(parametro_busqueda)).count() == len(results)

        parametro_busqueda = 'False'
        response = self.client.get('/api/caja/?incluir_estudio={0}'.format(parametro_busqueda))
        results = json.loads(response.content).get('results')

        for result in results:
            assert result['estudio'] is None

        assert MovimientoCaja.objects.count() - MovimientoCaja.objects.filter(estudio__isnull=strtobool(parametro_busqueda)).count() == len(results)
