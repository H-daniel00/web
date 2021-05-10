# pylint: disable=no-name-in-module, import-error
import json
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from caja.models import MovimientoCaja, TipoMovimientoCaja
from caja.serializers import MovimientoCajaImprimirSerializer
from medico.models import Medico
from estudio.models import Estudio
from distutils.util import strtobool
from datetime import datetime, date
from decimal import Decimal

class CrearMovimientosTest(TestCase):
    fixtures = ['caja.json', 'medicos.json', 'pacientes.json', 'practicas.json', 'obras_sociales.json',
        'anestesistas.json', 'presentaciones.json', 'comprobantes.json', 'estudios.json', 'medicamentos.json']
    
    def setUp(self):
        self.user = User.objects.create_user(username='walter', password='xx11', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='walter', password='xx11')

        self.estudio_id = Estudio.objects.first().id
        self.cantidad_movimientos = MovimientoCaja.objects.count()
        self.ultimo_monto = MovimientoCaja.objects.last().monto_acumulado

        self.montos = ['10.00', '1.99']
        self.conceptos = ['qwerty', 'wasd']
        self.tipos_id = [TipoMovimientoCaja.objects.first().id, TipoMovimientoCaja.objects.last().id]
        self.medicos_id = [Medico.objects.first().id, Medico.objects.last().id]

        self.movimientos = [
            {
                'concepto': self.conceptos[0],
                'tipo_id': self.tipos_id[0],
                'medico_id': self.medicos_id[0],
                'monto': self.montos[0],
            },
            {
                'concepto': self.conceptos[1],
                'tipo_id': self.tipos_id[1],
                'medico_id': self.medicos_id[1],
                'monto': self.montos[1],
            }
        ]
    
    def test_crear_un_movimiento_funciona(self):
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': [
                self.movimientos[0]
            ],
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        nuevo_movimiento = MovimientoCaja.objects.last()

        assert response.status_code == status.HTTP_201_CREATED
        assert self.cantidad_movimientos + 1 == MovimientoCaja.objects.count()

        assert nuevo_movimiento.monto_acumulado == self.ultimo_monto + Decimal(self.montos[0])
        assert nuevo_movimiento.estudio.id == self.estudio_id
        assert nuevo_movimiento.medico.id == self.medicos_id[0]
        assert nuevo_movimiento.tipo.id == self.tipos_id[0]

    def test_crear_movimientos_funciona(self):
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': self.movimientos,
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        assert self.cantidad_movimientos + 2 == MovimientoCaja.objects.count()

        monto =  self.ultimo_monto + Decimal(self.montos[0]) + Decimal(self.montos[1])
        assert MovimientoCaja.objects.last().monto_acumulado == monto

    def test_crear_movimiento_funciona_con_monto_negativo(self):
        monto_negativo = '-1.22'
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': [
                self.movimientos[0],
                {
                    **self.movimientos[1],
                    'monto': monto_negativo,
                }
            ]
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        assert self.cantidad_movimientos + 2 == MovimientoCaja.objects.count()

        monto =  self.ultimo_monto + Decimal(self.montos[0]) + Decimal(monto_negativo)
        assert MovimientoCaja.objects.last().monto_acumulado == monto

    def test_crear_movimiento_funciona_sin_algunos_campos(self):
        datos = {
            'estudio_id': '',
            'movimientos': [
                {
                    **self.movimientos[0],
                    'concepto': '',
                    'medico_id': '',
                },
            ],
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        assert self.cantidad_movimientos + 1 == MovimientoCaja.objects.count()
        
        nuevo_movimiento = MovimientoCaja.objects.last()
        assert nuevo_movimiento.estudio == None
        assert nuevo_movimiento.medico == None
        assert nuevo_movimiento.concepto == ''

    def test_crear_movimientos_falla_sin_monto(self):
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': [
                {
                    **self.movimientos[0],
                    'monto': '',
                },
                self.movimientos[1],
            ],
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        assert self.cantidad_movimientos == MovimientoCaja.objects.count()

    def test_crear_movimientos_funciona_con_monto_nulo(self):
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': [
                self.movimientos[0],
                {
                    **self.movimientos[1],
                    'monto': '0.00',
                }
            ],
        }
        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        assert self.cantidad_movimientos + 2 == MovimientoCaja.objects.count()
        
    def test_crear_movimientos_falla_con_tipo_erroneo(self):
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': [
                self.movimientos[0],
                {
                    **self.movimientos[1],
                    'medico_id': 'a',
                }
            ],
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.cantidad_movimientos == MovimientoCaja.objects.count()

        datos['estudio_id'] = 'a'
        datos['movimientos'][1]['medico_id'] =  self.medicos_id[1]

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.cantidad_movimientos == MovimientoCaja.objects.count()

        datos['estudio_id'] = self.estudio_id
        datos['movimientos'][1]['tipo_id'] = 'a'

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.cantidad_movimientos == MovimientoCaja.objects.count()

        datos['movimientos'][1]['tipo_id'] = self.tipos_id[1]
        datos['movimientos'][1]['monto'] = 'a'

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.cantidad_movimientos == MovimientoCaja.objects.count()

        datos['movimientos'][1]['monto'] = self.montos[1]
        
        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        assert self.cantidad_movimientos + 2 == MovimientoCaja.objects.count()

    def test_crear_movimientos_falla_sin_tipo(self):
        datos = {
            'estudio_id': self.estudio_id,
            'movimientos': [
                self.movimientos[0],
                {
                    **self.movimientos[1],
                    'tipo_id': '',
                }
            ],
        }

        response = self.client.post('/api/caja/', data=json.dumps(datos),
                                content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.cantidad_movimientos == MovimientoCaja.objects.count()

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
        for medico_id in (1, 2): # Con los fixtures que hay con esto se prueban los dos casos
            response = self.client.get('/api/caja/?medico={0}'.format(medico_id))
            results = json.loads(response.content).get('results')
        
            for result in results:
                assert result['medico']['id'] == medico_id or result['estudio']['medico']['id'] == medico_id

            cant_movimientos = MovimientoCaja.objects.filter(Q(medico__id=medico_id) | Q(estudio__medico__id=medico_id))
            assert cant_movimientos.count() == len(results)

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
    
    def test_filtro_paciente_funciona(self):
        paciente_id = 1
        response = self.client.get('/api/caja/?paciente={0}'.format(paciente_id))
        results = json.loads(response.content).get('results')

        assert len(results) > 0

        for result in results:
            assert paciente_id == result['estudio']['paciente']['id']


class ImprimirCajaTest(TestCase):
    fixtures = ['caja.json', 'medicos.json', 'pacientes.json', 'practicas.json', 'obras_sociales.json',
        'anestesistas.json', 'presentaciones.json', 'comprobantes.json', 'estudios.json', 'medicamentos.json']

    def setUp(self):
        self.user = User.objects.create_user(username='walter', password='xx11', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='walter', password='xx11')

    def test_serializer_funciona(self):
        movimientos = MovimientoCaja.objects.all()
        movimientos_serializer = MovimientoCajaImprimirSerializer(movimientos, many=True).data

        assert movimientos.count() == len(movimientos_serializer)

        for mov, mov_serializer in zip(movimientos, movimientos_serializer):
            assert str(mov.monto) == mov_serializer['monto']
            assert str(mov.monto_acumulado) == mov_serializer['monto_acumulado']
            assert mov.hora == mov_serializer['hora']
            assert mov.concepto == mov_serializer['concepto']
            assert str(mov.tipo) == mov_serializer['tipo']
            
            medico = mov.medico
            if mov.estudio:
                assert str(mov.estudio.obra_social) == mov_serializer['obra_social']
                assert str(mov.estudio.practica) == mov_serializer['practica']
                medico = medico or mov.estudio.medico
            
            if medico:
                assert str(medico) == mov_serializer['medico']

    def test_serializer_rellena_los_campos_opcionales(self):
        movimiento = MovimientoCaja(concepto='', fecha=date.today(), hora='00:00', tipo=TipoMovimientoCaja.objects.first())
        movimiento_serializer = MovimientoCajaImprimirSerializer(movimiento).data

        assert movimiento_serializer['concepto'] == ''
        assert movimiento_serializer['paciente'] == ''
        assert movimiento_serializer['obra_social'] == ''
        assert movimiento_serializer['medico'] == ''
        assert movimiento_serializer['practica'] == ''

    def test_serializer_elige_el_medico_correctamente(self):
        movimiento = MovimientoCaja.objects.first()
        medico = Medico.objects.first()
        medico_estudio = Medico.objects.get(pk=2)

        assert medico != medico_estudio

        movimiento.medico = medico
        movimiento_serializer = MovimientoCajaImprimirSerializer(movimiento).data
        assert movimiento_serializer['medico'] == str(medico)

        movimiento.medico = None
        movimiento.estudio = Estudio.objects.first()
        movimiento.estudio.medico = medico_estudio
        movimiento_serializer = MovimientoCajaImprimirSerializer(movimiento).data
        assert movimiento_serializer['medico'] == str(medico_estudio)

        movimiento.medico = medico
        movimiento_serializer = MovimientoCajaImprimirSerializer(movimiento).data

        assert movimiento_serializer['medico'] == str(medico)
