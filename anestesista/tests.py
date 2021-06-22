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

    def setUp(self):
        self.user = User.objects.create_user(username='walter', password='xx11', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='walter', password='xx11')

        self.anestesista = Anestesista.objects.get(id = 2)
        self.today = date.today()
        self.anio = 2013
        self.sucursal = 1

    def test_estudios_pacientes_diferenciados_sin_complejidad(self):
        mes = 11

        estudios = Estudio.objects.filter(
            anestesista=self.anestesista,
            fecha__year=self.anio,
            fecha__month=mes,
            sucursal=self.sucursal).order_by('fecha','paciente','obra_social')
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(self.today.year - 80, self.today.month, self.today.day)
            paciente.save()

        response = self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(self.anestesista.id, self.anio, mes, self.sucursal))
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        
        assert results['anestesista'] == AnestesistaSerializer(self.anestesista).data
        assert results['anio'] == self.anio
        assert results['mes'] == mes
        
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

    def test_estudios_pacientes_no_diferenciados_sin_complejidad(self):
        mes = 10

        estudios = Estudio.objects.filter(anestesista=self.anestesista,
        fecha__year=self.anio,
        fecha__month=mes,
        sucursal=self.sucursal).order_by('fecha','paciente','obra_social')
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(self.today.year - 20, self.today.month, self.today.day)
            paciente.save()

        response = self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(self.anestesista.id, self.anio, mes, self.sucursal))
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.anestesista).data
        assert results['anio'] == self.anio
        assert results['mes'] == mes

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

    def test_estudios_pacientes_no_diferenciados_con_complejidad_ara(self):
        mes = 9

        estudios = Estudio.objects.filter(anestesista=self.anestesista,
        fecha__year=self.anio,
        fecha__month=mes,
        sucursal=self.sucursal).order_by('fecha','paciente','obra_social')
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(self.today.year - 20, self.today.month, self.today.day)
            paciente.save()

        response = self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(self.anestesista.id, self.anio, mes, self.sucursal))
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.anestesista).data
        assert results['anio'] == self.anio
        assert results['mes'] == mes

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

    def test_estudios_pacientes_diferenciados_con_complejidad_ara(self):
        mes = 9

        estudios = Estudio.objects.filter(anestesista=self.anestesista,
        fecha__year=self.anio,
        fecha__month=mes,
        sucursal=self.sucursal).order_by('fecha','paciente','obra_social')
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(self.today.year - 10, self.today.month, self.today.day)
            paciente.save()

        response = self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(self.anestesista.id, self.anio, mes, self.sucursal))
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.anestesista).data
        assert results['anio'] == self.anio
        assert results['mes'] == mes

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

    def test_estudios_pacientes_diferenciados_con_complejidad_no_ara(self):
        mes = 9

        estudios = Estudio.objects.filter(anestesista=self.anestesista,
        fecha__year=self.anio,
        fecha__month=mes,
        sucursal=self.sucursal).order_by('fecha','paciente','obra_social')
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(self.today.year - 10, self.today.month, self.today.day)
            paciente.save()
            estudio.obra_social = ObraSocial.objects.get(pk=1)
            estudio.save()

        response = self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(self.anestesista.id, self.anio, mes, self.sucursal))
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.anestesista).data
        assert results['anio'] == self.anio
        assert results['mes'] == mes

        assert results['lineas_ARA'] == []
        assert results['totales_ara'] == {}

        assert results['totales_no_ara'] == {'iva2100': 3690.03}
        assert results['subtotales_no_ara'] == {'iva2100': 3049.61}
        assert results['totales_iva_no_ara'] == {'iva2100': 640.42}

        no_ara = [{
            'fecha': str(estudios.first().fecha),
            'paciente': PacienteSerializer(estudios.first().paciente).data,
            'obra_social': ObraSocialSerializer(estudios.first().obra_social).data,
            'estudios': EstudioSerializer(estudios, many=True).data,
            'comprobante': ComprobanteSerializer(estudios.first().presentacion.comprobante).data,
            'movimientos_caja': [], 'es_paciente_diferenciado': True,'formula': 'c1 + c2 - 20',
            'formula_valorizada': '2902 + 4336 - 20', 'importe': '9383.40', 'importe_con_iva': '0.00',
            'importe_iva': '0.00', 'sub_total': '6099.21', 'retencion': '3049.60', 'alicuota_iva': '21.00'
            }]
        assert results['lineas_no_ARA'] == no_ara

    def test_estudios_con_complejidad_ara_con_movimientos_asociados(self):
        mes = 9

        estudios = Estudio.objects.filter(anestesista=self.anestesista,
        fecha__year=self.anio,
        fecha__month=mes,
        sucursal=self.sucursal).order_by('fecha','paciente','obra_social')
        movimientos = []
        for ids in ((1, ID_COSEGURO), (3, ID_HONORARIO_ANESTESISTA)):
            movimiento = MovimientoCaja.objects.get(pk=ids[0])
            movimiento.estudio = estudios.first()
            movimiento.tipo = TipoMovimientoCaja.objects.get(pk=ids[1])
            movimiento.save()
            movimientos += [movimiento]
        for estudio in estudios:
            paciente = estudio.paciente
            paciente.fechaNacimiento = date(self.today.year - 10, self.today.month, self.today.day)
            paciente.save()

        response = self.client.get('/api/anestesista/{0}/pago/{1}/{2}/?sucursal={3}'.format(self.anestesista.id, self.anio, mes, self.sucursal))
        results = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK

        assert results['anestesista'] == AnestesistaSerializer(self.anestesista).data
        assert results['anio'] == self.anio
        assert results['mes'] == mes

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
