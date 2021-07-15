from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework import status
import json

from anestesista.models import Anestesista
from anestesista.serializers import AnestesistaSerializer, EstudioSerializer
from estudio.models import Estudio
from obra_social.models import ObraSocial
from obra_social.serializers import ObraSocialSerializer
from caja.models import MovimientoCaja, TipoMovimientoCaja, ID_COSEGURO, ID_HONORARIO_ANESTESISTA
from caja.serializers import MovimientoCajaSerializer
from paciente.serializers import PacienteSerializer
from comprobante.serializers import ComprobanteSerializer

from datetime import date

class GenerarVistaNuevoPagoTest(TestCase):
    fixtures = ['caja.json', 'pacientes.json', 'medicos.json', 'practicas.json', 'obras_sociales.json',
        'anestesistas.json', 'presentaciones.json', 'comprobantes.json', 'estudios.json', 'medicamentos.json']

    def query_generar_nuevo_pago(self, anestesista, fecha__year, fecha__month, sucursal):
        return self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(
            anestesista.id, fecha__year, fecha__month, sucursal))

    def modificar_estudios(self, estudios, edad_paciente, today, obra_social=False):
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(today.year - edad_paciente, today.month, today.day)
            paciente.save()
            if obra_social:
                estudio.obra_social = obra_social
            estudio.save()

    def setUp(self):
        self.user = User.objects.create_user(username='walter', password='xx11', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='walter', password='xx11')

        self.datos = {
            'anestesista': Anestesista.objects.get(id = 2),
            'fecha__year': 2013,
            'fecha__month': 1,
            'sucursal': 1
        }
        self.today = date.today()

    def test_estudios_pacientes_diferenciados_sin_complejidad_funciona(self):
        self.datos['fecha__month'] = 11

        estudios = Estudio.objects.filter(**self.datos).order_by('fecha', 'paciente', 'obra_social')
        self.modificar_estudios(estudios, 80, self.today)

        response = self.query_generar_nuevo_pago(**self.datos)
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.datos['anestesista']).data
        assert results['anio'] == self.datos['fecha__year']
        assert results['mes'] == self.datos['fecha__month']

        empty_fields = ['totales_ara', 'totales_no_ara', 'subtotales_no_ara', 'totales_iva_no_ara']
        for field in empty_fields:
            assert results[field] == {}
        assert results['lineas_no_ARA'] == []

        ara = []
        for estudio in estudios:
            ara += [{
                'fecha': str(estudio.fecha),
                'paciente': PacienteSerializer(estudio.paciente).data,
                'obra_social': ObraSocialSerializer(estudio.obra_social).data,
                'estudios': [EstudioSerializer(estudio).data],
                'movimientos_caja': [], 'comprobante': None, 'es_paciente_diferenciado': True,
                'formula': '0', 'formula_valorizada': '0', 'importe': '0.00', 'importe_con_iva': '0.00',
                'importe_iva': '0.00', 'sub_total': '0.00', 'retencion': '0.00', 'alicuota_iva': '0.00'
                }]
        assert results['lineas_ARA'] == ara

    def test_estudios_pacientes_no_diferenciados_sin_complejidad_funciona(self):
        self.datos['fecha__month'] = 10

        estudios = Estudio.objects.filter(**self.datos).order_by('fecha', 'paciente', 'obra_social')
        self.modificar_estudios(estudios, 20, self.today)

        response = self.query_generar_nuevo_pago(**self.datos)
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.datos['anestesista']).data
        assert results['anio'] == self.datos['fecha__year']
        assert results['mes'] == self.datos['fecha__month']

        empty_fields = ['totales_ara', 'totales_no_ara', 'subtotales_no_ara', 'totales_iva_no_ara']
        for field in empty_fields:
            assert results[field] == {}
        assert results['lineas_no_ARA'] == []

        ara = []
        for estudio in estudios:
            ara += [{
                'fecha': str(estudio.fecha),
                'paciente': PacienteSerializer(estudio.paciente).data,
                'obra_social': ObraSocialSerializer(estudio.obra_social).data,
                'estudios': [EstudioSerializer(estudio).data],
                'movimientos_caja': [], 'comprobante': None, 'es_paciente_diferenciado': False,
                'formula': '0', 'formula_valorizada': '0', 'importe': '0.00', 'importe_con_iva': '0.00',
                'importe_iva': '0.00', 'sub_total': '0.00', 'retencion': '0.00', 'alicuota_iva': '0.00'
                }]
        assert results['lineas_ARA'] == ara

    def test_estudios_pacientes_no_diferenciados_con_complejidad_ara_funciona(self):
        self.datos['fecha__month'] = 9

        estudios = Estudio.objects.filter(**self.datos).order_by('fecha', 'paciente', 'obra_social')
        self.modificar_estudios(estudios, 20, self.today)

        response = self.query_generar_nuevo_pago(**self.datos)
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.datos['anestesista']).data
        assert results['anio'] == self.datos['fecha__year']
        assert results['mes'] == self.datos['fecha__month']

        empty_fields = ['totales_no_ara', 'subtotales_no_ara', 'totales_iva_no_ara']
        for field in empty_fields:
            assert results[field] == {}
        assert results['lineas_no_ARA'] == []

        assert results['totales_ara'] == {'subtotal': 2345.85, 'iva': 492.63, 'total': 2838.48}
        ara = [{
            'fecha': str(estudios.first().fecha),
            'paciente': PacienteSerializer(estudios.first().paciente).data,
            'obra_social': ObraSocialSerializer(estudios.first().obra_social).data,
            'estudios': EstudioSerializer(estudios, many=True).data,
            'movimientos_caja': [], 'comprobante': None, 'es_paciente_diferenciado': False,
            'formula': 'c1 + c2 - 20', 'formula_valorizada': '2902 + 4336 - 20', 'importe': '7218.00', 'importe_con_iva': '0.00',
            'importe_iva': '0.00', 'sub_total': '4691.70', 'retencion': '2345.85', 'alicuota_iva': '21.00'
            }]
        assert results['lineas_ARA'] == ara

    def test_estudios_pacientes_diferenciados_con_complejidad_ara_funciona(self):
        self.datos['fecha__month'] = 9

        estudios = Estudio.objects.filter(**self.datos).order_by('fecha', 'paciente', 'obra_social')
        self.modificar_estudios(estudios, 10, self.today)

        response = self.query_generar_nuevo_pago(**self.datos)
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.datos['anestesista']).data
        assert results['anio'] == self.datos['fecha__year']
        assert results['mes'] == self.datos['fecha__month']

        empty_fields = ['totales_no_ara', 'subtotales_no_ara', 'totales_iva_no_ara']
        for field in empty_fields:
            assert results[field] == {}
        assert results['lineas_no_ARA'] == []

        assert results['totales_ara'] == {'subtotal': 3049.61, 'iva': 640.42, 'total': 3690.03}
        ara = [{
            'fecha': str(estudios.first().fecha),
            'paciente': PacienteSerializer(estudios.first().paciente).data,
            'obra_social': ObraSocialSerializer(estudios.first().obra_social).data,
            'estudios': EstudioSerializer(estudios, many=True).data,
            'movimientos_caja': [], 'comprobante': None, 'es_paciente_diferenciado': True,
            'formula': 'c1 + c2 - 20', 'formula_valorizada': '2902 + 4336 - 20', 'importe': '9383.40', 'importe_con_iva': '0.00',
            'importe_iva': '0.00', 'sub_total': '6099.21', 'retencion': '3049.60', 'alicuota_iva': '21.00'
            }]
        assert results['lineas_ARA'] == ara

    def test_estudios_pacientes_diferenciados_con_complejidad_no_ara_funciona(self):
        self.datos['fecha__month'] = 9

        estudios = Estudio.objects.filter(**self.datos).order_by('fecha', 'paciente', 'obra_social')
        self.modificar_estudios(estudios, 10, self.today, ObraSocial.objects.get(pk=1))

        response = self.query_generar_nuevo_pago(**self.datos)
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.datos['anestesista']).data
        assert results['anio'] == self.datos['fecha__year']
        assert results['mes'] == self.datos['fecha__month']

        assert results['lineas_ARA'] == []
        assert results['totales_ara'] == {}

        assert results['totales_no_ara'] == {'iva2100': 3690.03}
        assert results['subtotales_no_ara'] == {'iva2100': 3049.61}
        assert results['totales_iva_no_ara'] == {'iva2100': 640.42}

        estudios1 = list(map(lambda x: dict(x), EstudioSerializer(estudios, many=True).data))
        for estudio in estudios1:
            estudio['practica'] = dict(estudio['practica'])
        no_ara = [{
            'fecha': str(estudios.first().fecha),
            'paciente': dict(PacienteSerializer(estudios.first().paciente).data),
            'obra_social': dict(ObraSocialSerializer(estudios.first().obra_social).data),
            'estudios': estudios1,
            'comprobante': dict(ComprobanteSerializer(estudios.first().presentacion.comprobante).data),
            'movimientos_caja': [], 'es_paciente_diferenciado': True,'formula': 'c1 + c2 - 20',
            'formula_valorizada': '2902 + 4336 - 20', 'importe': '9383.40', 'importe_con_iva': '0.00',
            'importe_iva': '0.00', 'sub_total': '6099.21', 'retencion': '3049.60', 'alicuota_iva': '21.00'
            }]
        no_ara[0]['comprobante']['tipo_comprobante'] = dict(no_ara[0]['comprobante']['tipo_comprobante'])
        no_ara[0]['comprobante']['gravado'] = dict(no_ara[0]['comprobante']['gravado'])

        assert results['lineas_no_ARA'] == no_ara

    def test_estudios_con_complejidad_ara_con_movimientos_asociados_funciona(self):
        self.datos['fecha__month'] = 9

        estudios = Estudio.objects.filter(**self.datos).order_by('fecha', 'paciente', 'obra_social')
        movimientos = []
        for ids in ((1, ID_COSEGURO), (3, ID_HONORARIO_ANESTESISTA)):
            movimiento = MovimientoCaja.objects.get(pk=ids[0])
            movimiento.estudio = estudios.first()
            movimiento.tipo = TipoMovimientoCaja.objects.get(pk=ids[1])
            movimiento.save()
            movimientos += [movimiento]
        self.modificar_estudios(estudios, 10, self.today)

        response = self.query_generar_nuevo_pago(**self.datos)
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.datos['anestesista']).data
        assert results['anio'] == self.datos['fecha__year']
        assert results['mes'] == self.datos['fecha__month']

        assert results['totales_iva_no_ara'] == {'iva00': 0.0}
        assert results['totales_no_ara'] == {'iva00': 357.18}
        assert results['subtotales_no_ara'] == {'iva00': 357.18}
        assert results['totales_ara'] == {'subtotal': 2692.43, 'iva': 565.42, 'total': 3257.85}

        fecha = str(estudios.first().fecha)
        paciente = PacienteSerializer(estudios.first().paciente).data
        obra_social = ObraSocialSerializer(estudios.first().obra_social).data
        estudios = list(map(lambda x: dict(x), EstudioSerializer(estudios, many=True).data))
        for estudio in estudios:
            estudio['practica'] = dict(estudio['practica'])
        movimientos_caja = list(map(lambda x: dict(x), MovimientoCajaSerializer(movimientos, many=True).data))
        for movimiento in movimientos_caja:
            movimiento['tipo'] = dict(movimiento['tipo'])

        no_ara = [{
            'fecha': fecha, 'paciente': paciente, 'obra_social': obra_social, 'estudios': estudios,
            'movimientos_caja': movimientos_caja, 'comprobante': None, 'es_paciente_diferenciado': True,
            'formula': 'c1 + c2 - 20', 'formula_valorizada': '2902 + 4336 - 20', 'importe': '1099.00', 'importe_con_iva': '0.00',
            'importe_iva': '0.00', 'sub_total': '714.35', 'retencion': '357.18', 'alicuota_iva': '0.00'
        }]
        assert results['lineas_no_ARA'] == no_ara

        ara = [{
            'fecha': fecha, 'paciente': paciente, 'obra_social': obra_social,
            'estudios': estudios, 'movimientos_caja': movimientos_caja, 'comprobante': None, 'es_paciente_diferenciado': True,
            'formula': 'c1 + c2 - 20', 'formula_valorizada': '2902 + 4336 - 20', 'importe': '8284.40', 'importe_con_iva': '0.00',
            'importe_iva': '0.00', 'sub_total': '5384.86', 'retencion': '2692.43', 'alicuota_iva': '21.00'
            }]
        assert results['lineas_ARA'] == ara
