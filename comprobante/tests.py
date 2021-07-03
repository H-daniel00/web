from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from mock import patch
from comprobante.afip import AfipError
from .models import LineaDeComprobante, Gravado, TipoComprobante, Comprobante
from .serializers import CrearComprobanteAFIPSerializer, CrearLineaDeComprobanteSerializer

class TestCrearLineaSerializer(TestCase):
    fixtures = ['comprobantes.json']

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', is_superuser=True)
        self.cliente = Client(HTTP_GET='localhost')
        self.client.login(username='test', password='test')
        self.linea_data = {
            'concepto': 'hola',
            'gravado_id': '2',
            'importe_neto': '500'
        }


    def test_crear_linea_serializer_crea_objeto_linea(self):
        linea_serializer = CrearLineaDeComprobanteSerializer(data=self.linea_data)
        
        assert isinstance(linea_serializer, CrearLineaDeComprobanteSerializer)
        assert linea_serializer.is_valid()
        
        linea_db = linea_serializer.save()
        
        assert isinstance(linea_db, LineaDeComprobante)
        assert linea_db.concepto == self.linea_data['concepto']
        assert linea_db.importe_neto == Decimal(self.linea_data['importe_neto'])

    def test_crear_linea_serializer_calcula_correctamente_iva(self):
        linea_serializer = CrearLineaDeComprobanteSerializer(data=self.linea_data)
        
        assert linea_serializer.is_valid()
        
        linea = linea_serializer.save()
        importe_neto = Decimal(self.linea_data['importe_neto'])
        porcentaje_iva = Gravado.objects.get(pk=self.linea_data['gravado_id']).porcentaje
        
        assert linea.iva == importe_neto * porcentaje_iva / Decimal(100)

    def test_crear_linea_serializer_calcula_correctamente_total(self):
        linea_serializer = CrearLineaDeComprobanteSerializer(data=self.linea_data)
        
        assert linea_serializer.is_valid()
        
        linea = linea_serializer.save()
        importe_neto = Decimal(self.linea_data['importe_neto'])
        porcentaje_iva = Gravado.objects.get(pk=self.linea_data['gravado_id']).porcentaje
        
        total = importe_neto + importe_neto * porcentaje_iva / Decimal(100)
        
        assert linea.sub_total == total

    def test_crear_linea_serializer_no_valido_si_id_iva_no_existe(self):
        linea_data = {**self.linea_data}
        linea_data['gravado_id'] = Gravado.objects.last().id + 1
        linea_serializer = CrearLineaDeComprobanteSerializer(data=linea_data)

        assert not linea_serializer.is_valid()
        assert 'gravado_id' in linea_serializer.errors

class TestCrearComprobanteSerializer(TestCase):
    fixtures = ['comprobantes.json']

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', is_superuser=True)
        self.cliente = Client(HTTP_GET='localhost')
        self.client.login(username='test', password='test')
        self.lineas_data = [
                {
                    'concepto': 'Esta es la primera linea',
                    'importe_neto': 50
                },
                {
                    'concepto': 'Esta es la segunda linea',
                    'importe_neto': 60
                }
            ]
        self.comprobante_data = {
            'tipo_comprobante_id': 1,
            'sub_tipo': 'A',
            'responsable': 'Cedir',
            'gravado_id': '1',
            'nombre_cliente': 'Homero',
            'domicilio_cliente': 'Avenida Siempreviva 123',
            'nro_cuit': '20420874120',
            'condicion_fiscal': 'RESPONSABLE INSCRIPTO',
        }
    
    @patch('comprobante.serializers.Afip')
    def test_comprobante_afip_serializer_funciona_si_no_envian_lineas(self, afip_mock):
        afip = afip_mock()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['neto'] = 100
        comprobante_data['concepto'] = 'Este es un concepto'
        
        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert comprobante_serializer.is_valid()
        comprobante = comprobante_serializer.save()

        neto = comprobante_data['neto']

        iva = Gravado.objects.get(pk=comprobante_data['gravado_id']).porcentaje * neto

        total = neto + neto * iva / Decimal(100)

        afip.emitir_comprobante.assert_called_once()
        assert comprobante.total_facturado == total
        assert comprobante.tipo_comprobante.id == comprobante_data['tipo_comprobante_id']
        assert comprobante.sub_tipo == comprobante_data['sub_tipo']
        assert comprobante.nombre_cliente == comprobante_data['nombre_cliente']

        linea = LineaDeComprobante.objects.get(comprobante=comprobante)

        assert linea.importe_neto == neto
        assert linea.sub_total == total
        assert linea.concepto == comprobante_data['concepto']

    @patch('comprobante.serializers.Afip')
    def test_comprobante_afip_serializer_funciona_si_envian_lineas(self, afip_mock):
        afip = afip_mock()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['lineas'] = self.lineas_data
        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert comprobante_serializer.is_valid()
        comprobante = comprobante_serializer.save()

        neto = sum(l['importe_neto'] for l in comprobante_data['lineas'])

        gravado = Gravado.objects.get(pk=comprobante_data['gravado_id'])

        iva = gravado.porcentaje * neto

        total = neto + neto * iva / Decimal(100)

        afip.emitir_comprobante.assert_called_once()
        assert comprobante.total_facturado == total
        assert comprobante.tipo_comprobante.id == comprobante_data['tipo_comprobante_id']
        assert comprobante.sub_tipo == comprobante_data['sub_tipo']
        assert comprobante.nombre_cliente == comprobante_data['nombre_cliente']

        lineas = LineaDeComprobante.objects.filter(comprobante=comprobante).order_by('id')
        
        assert lineas.count() == len(comprobante_data['lineas'])

        for i in range(lineas.count()):
            linea_data = comprobante_data['lineas'][i]

            assert lineas[i].importe_neto == linea_data['importe_neto']
            assert lineas[i].iva == linea_data['importe_neto'] * gravado.porcentaje / Decimal(100)
            assert lineas[i].concepto == linea_data['concepto']

    @patch('comprobante.serializers.Afip')
    def test_crear_comprobante_error_si_gravado_id_no_existe(self, afip_mock):
        afip = afip_mock()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['gravado_id'] = Gravado.objects.last().id + 1
        comprobante_data['lineas'] = self.lineas_data

        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert not comprobante_serializer.is_valid()
        assert 'lineas' in comprobante_serializer.errors
        assert 'gravado_id' in comprobante_serializer.errors['lineas']

    @patch('comprobante.serializers.Afip')
    def test_crear_comprobante_error_si_tipo_comprobante_id_no_existe(self, afip_mock):
        afip = afip_mock()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['tipo_comprobante_id'] = TipoComprobante.objects.last().id + 1
        comprobante_data['lineas'] = self.lineas_data

        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert not comprobante_serializer.is_valid()
        assert 'tipo_comprobante_id' in comprobante_serializer.errors

    @patch('comprobante.serializers.Afip')
    def test_crear_comprobante_error_si_responsable_no_existe(self, afip_mock):
        afip = afip_mock()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['responsable'] = 'no_existe'
        comprobante_data['lineas'] = self.lineas_data

        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert not comprobante_serializer.is_valid()
        assert 'responsable' in comprobante_serializer.errors

    @patch('comprobante.serializers.Afip')
    def test_crear_comprobante_error_si_sub_tipo_no_existe(self, afip_mock):
        afip = afip_mock()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['sub_tipo'] = 'OTRO'
        comprobante_data['lineas'] = self.lineas_data

        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert not comprobante_serializer.is_valid()
        assert 'sub_tipo' in comprobante_serializer.errors

    @patch('comprobante.serializers.Afip')
    def test_crear_comprobante_no_guarda_en_db_si_afip_lanza_excepcion(self, afip_mock):
        afip = afip_mock()
        cant_original_comprobante = Comprobante.objects.count()
        cant_original_lineas = LineaDeComprobante.objects.count()
        comprobante_data = {**self.comprobante_data}
        comprobante_data['lineas'] = self.lineas_data

        afip.emitir_comprobante.side_effect = AfipError

        comprobante_serializer = CrearComprobanteAFIPSerializer(data=comprobante_data)

        assert comprobante_serializer.is_valid()

        with self.assertRaises(AfipError):
            comprobante_serializer.save()

        afip.emitir_comprobante.assert_called_once()
        assert cant_original_comprobante == Comprobante.objects.count()
        assert cant_original_lineas == LineaDeComprobante.objects.count()
