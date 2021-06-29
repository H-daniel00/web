from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework import status
from mock import patch
import json

from comprobante.models import Comprobante, TipoComprobante, ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO

class TestViews(TestCase):

    fixtures = ['comprobantes.json']

    def setUp(self):
        self.user = User.objects.create_user(username='usuario', password='xxxxxx1', is_superuser=True)
        self.client = Client(HTTP_POST='localhost')
        self.client.login(username='usuario', password='xxxxxx1')

    @patch('comprobante.comprobante_asociado.Afip')
    def test_cliente_obtiene_el_json_del_comprobante_cuando_genera_un_comprobante_asociado(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 14
        response = self.client.post('/api/comprobante/crear_comprobante_asociado', {'id-comprobante-asociado': 1, 'importe': 200, 'concepto': '', 'tipo': 4})

        comp = response.data['data']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comp['numero'], 14)
        self.assertEqual(comp['tipo_comprobante']['nombre'], (TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)).nombre)
        self.assertEqual(comp['tipo_comprobante']['id'], ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        self.assertEqual(comp['total_facturado'], '200.00')

        response = self.client.post('/api/comprobante/crear_comprobante_asociado', {'id-comprobante-asociado': 1, 'importe': 200, 'concepto': 'ajustes', 'tipo': 4})

        comp = response.data['data']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comp['numero'], 14)
        self.assertEqual(comp['tipo_comprobante']['nombre'], (TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)).nombre)
        self.assertEqual(comp['tipo_comprobante']['id'], ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        self.assertEqual(comp['total_facturado'], '200.00')

    def test_informe_ventas_ok(self):

        response = self.client.get("/comprobante/informe/ventas/cedir/2019/09/?responsable=cedir&anio=2019&mes=09")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], 'application/x-zip-compressed')

    def test_filtro_por_nombre_cliente_funciona(self):
        keywords = 'Planta Springfield'
        
        response = self.client.get(f'/api/comprobante?nombre_cliente={keywords}')
        assert response.status_code == status.HTTP_200_OK
        
        results = json.loads(response.content).get('results')
        for comprobante in results:
            for word in keywords.split():
                assert word in comprobante['nombre_cliente']

    def test_filtro_por_cuit_funciona(self):
        cuit = '11'
        
        response = self.client.get(f'/api/comprobante?nombre_cliente={cuit}')
        assert response.status_code == status.HTTP_200_OK
        
        results = json.loads(response.content).get('results')
        for comprobante in results:
            assert cuit in comprobante['cuit']

    def test_filtro_por_numero_funciona(self):
        numero = '2'
        
        response = self.client.get(f'/api/comprobante?nombre_cliente={numero}')
        assert response.status_code == status.HTTP_200_OK
        
        results = json.loads(response.content).get('results')
        for comprobante in results:
            assert numero == comprobante['numero']
