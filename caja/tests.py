# pylint: disable=no-name-in-module, import-error
from django.test import TestCase
from django.test import Client
from rest_framework import status
from django.contrib.auth.models import User
import json

from caja.models import MovimientoCaja, TipoMovimientoCaja, MontoAcumulado, ID_CONSULTORIO_1, ID_CONSULTORIO_2, ID_GENERAL
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
    
    def test_crear_movimientos_suma_monto_acumulado(self):
        datos = {
            'estudio_id': '',
            'movimientos': [
                {
                    **self.movimientos[0],
                    'tipo_id': ID_CONSULTORIO_1,
                    'medico_id': '',
                    'concepto': '',
                },
                {
                    **self.movimientos[1],
                    'tipo_id': ID_CONSULTORIO_2,
                    'medico_id': '',
                    'concepto': '',
                },
                {
                    'tipo_id': ID_GENERAL,
                    'monto': 55,
                    'medico_id': '',
                    'concepto': '',
                }
            ]
        }
        montos = [MontoAcumulado.objects.get(tipo__id=tipo).monto_acumulado
                    for tipo in (ID_CONSULTORIO_1, ID_CONSULTORIO_2, ID_GENERAL)]

        response = self.client.post('/api/caja/', data=json.dumps(datos), content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED

        montos_actualizados = [MontoAcumulado.objects.get(tipo__id=tipo).monto_acumulado
                    for tipo in (ID_CONSULTORIO_1, ID_CONSULTORIO_2, ID_GENERAL)]

        assert Decimal(self.montos[0]) + montos[0] == Decimal(montos_actualizados[0])
        assert Decimal(self.montos[1]) + montos[1] == Decimal(montos_actualizados[1])
        assert 55 + montos[2] == montos_actualizados[2]

class ListadoCajaTest(TestCase):
    fixtures = ['caja.json', 'pacientes.json', 'medicos.json', 'practicas.json', 'obras_sociales.json',
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
        for medico_id in (1, 2):
            response = self.client.get('/api/caja/?medico={0}'.format(medico_id))
            results = json.loads(response.content).get('results')
        
            for result in results:
                assert result['medico']['id'] == medico_id or result['estudio']['medico']['id'] == medico_id

            cant_movimientos = MovimientoCaja.objects.filter(medico__id=medico_id)
            assert cant_movimientos.count() == len(results)

    def test_filtro_fecha_funciona(self):
        fecha_inicial = '2019-02-01'
        fecha_final = '2019-02-08'
        response = self.client.get('/api/caja/?fecha_desde={0}&fecha_hasta={1}'.format(fecha_inicial, fecha_final))
        results = json.loads(response.content).get('results')

        for result in results:
            fecha = list(map(int, result['fecha'].split('/')))
            assert fecha[2] == 2019
            assert fecha[1] == 2
            assert 1 <= fecha[0] <= 8

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

    def test_montos_acumulados_funciona(self):
        response = self.client.get('/api/caja/montos_acumulados/')
        assert response.status_code == status.HTTP_200_OK

        montos = json.loads(response.content)

        assert Decimal(montos['consultorio_1']) == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        assert Decimal(montos['consultorio_2']) == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        assert Decimal(montos['general']) == MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

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
            assert str(mov.hora)[:5] == mov_serializer['hora']
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
        movimiento_serializer = MovimientoCajaImprimirSerializer(movimiento).data
        assert movimiento_serializer['medico'] == ''

class UpdateCajaTest(TestCase):
    fixtures = ['caja.json', 'pacientes.json', 'medicos.json', 'practicas.json', 'obras_sociales.json',
        'anestesistas.json', 'presentaciones.json', 'comprobantes.json', 'estudios.json', 'medicamentos.json']

    def setUp(self):
        self.user = User.objects.create_user(username='walter', password='xx11', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='walter', password='xx11')

        self.movimiento = MovimientoCaja.objects.first()
        self.url = '/api/caja/{0}/update_movimientos/'.format(self.movimiento.id)

        self.body = {'concepto': 'Concepto Nuevo', 'fecha': str(date.today()), 'hora': str(datetime.now().time()),
        'tipo': 2, 'estudio': 1, 'medico': 1, 'monto': "0.00", 'monto_acumulado': "0.00",
        'user': 'walter'
        }

        self.campos_id = ['tipo', 'estudio', 'medico']
        self.campos_fijos = ['hora', 'estudio', 'monto', 'fecha', 'user', 'monto_acumulado']
        self.campos_update = ['concepto', 'medico', 'tipo']

    def test_movimientos_update_solo_un_field_funciona(self):
        for key in self.campos_update:
            response = self.client.patch(self.url, data=json.dumps({key: self.body[key]}), content_type='application/json')
            assert response.status_code == status.HTTP_200_OK
            movimiento_update = MovimientoCaja.objects.get(pk=self.movimiento.id)
            assert getattr(self.movimiento, key, None) != getattr(movimiento_update, key, None)

    def tests_movimientos_update_actualiza_montos_acumulados_si_es_del_dia(self):
        self.movimiento.fecha = date.today()
        self.movimiento.save()

        self.body['tipo'] = ID_GENERAL
        montoConsultorio1 = MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        montoConsultorio2 = MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        montoGeneral = MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK

        assert montoConsultorio1 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        assert montoConsultorio2 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        assert montoGeneral == MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

        self.body['tipo'] = ID_CONSULTORIO_1

        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK

        assert montoConsultorio1 + self.movimiento.monto == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        assert montoConsultorio2 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        assert montoGeneral - self.movimiento.monto == MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

    def tests_movimientos_update_actualiza_montos_acumulados_si_no_es_del_dia(self):
        self.body['tipo'] = ID_GENERAL
        montoConsultorio1 = MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        montoConsultorio2 = MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        montoGeneral = MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK

        assert montoConsultorio1 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        assert montoConsultorio2 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        assert montoGeneral == MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

        self.body['tipo'] = ID_CONSULTORIO_1

        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK

        assert montoConsultorio1 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_1).monto_acumulado
        assert montoConsultorio2 == MontoAcumulado.objects.get(tipo__id=ID_CONSULTORIO_2).monto_acumulado
        assert montoGeneral == MontoAcumulado.objects.get(tipo__id=ID_GENERAL).monto_acumulado

    def test_movimientos_update_funciona(self):
        for key in self.campos_fijos:
            del self.body[key]

        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')

        assert response.status_code == status.HTTP_200_OK

        movimiento_update = MovimientoCaja.objects.get(pk=self.movimiento.id)

        for key in self.campos_fijos:
            assert getattr(self.movimiento, key, None) == getattr(movimiento_update, key, None)

        for key in self.campos_update:
            campoUpdate = getattr(movimiento_update, key, None)

            assert getattr(self.movimiento, key, None) != campoUpdate
            if key in self.campos_id:
                assert self.body[key] == campoUpdate.id
            else:
                assert self.body[key] == campoUpdate

    def test_movimientos_update_no_cambia_todos_los_campos(self):
        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')

        assert response.status_code == status.HTTP_200_OK

        movimiento_update = MovimientoCaja.objects.get(pk=self.movimiento.id)

        for key in self.campos_fijos:
            assert getattr(self.movimiento, key, None) == getattr(movimiento_update, key, None)

        for key in self.campos_update:
            campoUpdate = getattr(movimiento_update, key, None)
            assert getattr(self.movimiento, key, None) != campoUpdate
            if key in self.campos_id:
                assert self.body[key] == campoUpdate.id
            else:
                assert self.body[key] == campoUpdate

    def test_movimientos_update_quita_medico_field(self):
        response = self.client.patch(self.url, data=json.dumps(self.body), content_type='application/json')

        assert response.status_code == status.HTTP_200_OK

        self.movimiento = MovimientoCaja.objects.get(pk=self.movimiento.id)

        assert self.body['medico'] == self.movimiento.medico.id

        body = {'medico': ""}
        response = self.client.patch(self.url, data=json.dumps(body), content_type='application/json')

        assert response.status_code == status.HTTP_200_OK

        movimiento_update = MovimientoCaja.objects.get(pk=self.movimiento.id)

        assert movimiento_update.medico != self.movimiento.medico
        assert movimiento_update.medico == None
