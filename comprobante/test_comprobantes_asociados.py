from django.test import TestCase
from mock import patch
from datetime import date
from decimal import Decimal
from comprobante.comprobante_asociado import crear_comprobante_asociado, calcular_iva, TipoComprobanteAsociadoNoValidoException
from comprobante.afip import AfipErrorRed, AfipErrorValidacion
from comprobante.models import Comprobante, Gravado, TipoComprobante, LineaDeComprobante, \
    ID_TIPO_COMPROBANTE_FACTURA, ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA, \
    ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO, ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA, \
    ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO, ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA, \
    ID_TIPO_COMPROBANTE_LIQUIDACION

class TestComprobantesAsociados(TestCase):

    fixtures = ['comprobantes.json']
        
    @patch('comprobante.comprobante_asociado.Afip')
    def test_genera_nota_de_credito_si_se_envia_una_factura(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 10

        comp = Comprobante.objects.get(pk = 1)

        nuevo_comp = crear_comprobante_asociado(1, Decimal(200), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert nuevo_comp.nombre_cliente == comp.nombre_cliente
        assert nuevo_comp.nro_cuit == comp.nro_cuit
        assert nuevo_comp.responsable == comp.responsable
        assert nuevo_comp.condicion_fiscal == comp.condicion_fiscal
        assert nuevo_comp.total_facturado == Decimal(200).quantize(Decimal(10)**-2)
        assert nuevo_comp.tipo_comprobante == TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        assert nuevo_comp.nro_terminal == comp.nro_terminal

    @patch('comprobante.comprobante_asociado.Afip')
    def test_falla_crear_comprobante_asociado_si_es_liquidacion(self, mock):
        nuevo_comp = Comprobante.objects.get(pk = 1)
        nuevo_comp.tipo_comprobante = TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_LIQUIDACION)
        nuevo_comp.save()
        with self.assertRaises(TipoComprobanteAsociadoNoValidoException):
            crear_comprobante_asociado(1, Decimal(500), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

    @patch('comprobante.comprobante_asociado.Afip')
    def test_genera_nota_de_credito_si_se_envia_una_nota_de_debito(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 11
        
        comp = Comprobante.objects.get(pk = 1)
        comp.tipo_comprobante = TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO)
        comp.save()

        nuevo_comp = crear_comprobante_asociado(1, Decimal(300), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert nuevo_comp.nombre_cliente == comp.nombre_cliente
        assert nuevo_comp.nro_cuit == comp.nro_cuit
        assert nuevo_comp.responsable == comp.responsable
        assert nuevo_comp.condicion_fiscal == comp.condicion_fiscal
        assert nuevo_comp.total_facturado == Decimal(300).quantize(Decimal(10)**-2)
        assert nuevo_comp.tipo_comprobante == TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        assert nuevo_comp.nro_terminal == comp.nro_terminal
    
    @patch('comprobante.comprobante_asociado.Afip')
    def test_genera_nota_de_debito_si_se_envia_una_nota_de_credito(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 12
        
        comp = Comprobante.objects.get(pk = 1)
        comp.tipo_comprobante = TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        comp.save()
        nuevo_comp = crear_comprobante_asociado(1, Decimal(400), '', ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO)

        assert nuevo_comp.nombre_cliente == comp.nombre_cliente
        assert nuevo_comp.nro_cuit == comp.nro_cuit
        assert nuevo_comp.responsable == comp.responsable
        assert nuevo_comp.condicion_fiscal == comp.condicion_fiscal
        assert nuevo_comp.total_facturado == Decimal(400).quantize(Decimal(10)**-2)
        assert nuevo_comp.tipo_comprobante == TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO)
        assert nuevo_comp.nro_terminal == comp.nro_terminal

    @patch('comprobante.comprobante_asociado.Afip')
    def test_genera_nota_de_credito_electronica_si_se_envia_una_factura_electronica(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 10

        comp = Comprobante.objects.get(pk = 1)
        comp.tipo_comprobante = TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA)
        comp.save()

        nuevo_comp = crear_comprobante_asociado(1, Decimal(200), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA)

        assert nuevo_comp.nombre_cliente == comp.nombre_cliente
        assert nuevo_comp.nro_cuit == comp.nro_cuit
        assert nuevo_comp.responsable == comp.responsable
        assert nuevo_comp.condicion_fiscal == comp.condicion_fiscal
        assert nuevo_comp.total_facturado == Decimal(200).quantize(Decimal(10)**-2)
        assert nuevo_comp.tipo_comprobante == TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA)
        assert nuevo_comp.nro_terminal == comp.nro_terminal

    @patch('comprobante.comprobante_asociado.Afip')
    def test_genera_nota_de_credito_electronica_si_se_envia_una_nota_de_debito_electronica(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 11
        
        comp = Comprobante.objects.get(pk = 1)
        comp.tipo_comprobante = TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA)
        comp.save()

        nuevo_comp = crear_comprobante_asociado(1, Decimal(300), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA)

        assert nuevo_comp.nombre_cliente == comp.nombre_cliente
        assert nuevo_comp.nro_cuit == comp.nro_cuit
        assert nuevo_comp.responsable == comp.responsable
        assert nuevo_comp.condicion_fiscal == comp.condicion_fiscal
        assert nuevo_comp.total_facturado == Decimal(300).quantize(Decimal(10)**-2)
        assert nuevo_comp.tipo_comprobante == TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA)
        assert nuevo_comp.nro_terminal == comp.nro_terminal

    @patch('comprobante.comprobante_asociado.Afip')
    def test_genera_nota_de_debito_electronica_si_se_envia_una_nota_de_credito_electronica(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 12
        
        comp = Comprobante.objects.get(pk = 1)
        comp.tipo_comprobante = TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO_ELECTRONICA)
        comp.save()
        nuevo_comp = crear_comprobante_asociado(1, Decimal(400), '', ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA)

        assert nuevo_comp.nombre_cliente == comp.nombre_cliente
        assert nuevo_comp.nro_cuit == comp.nro_cuit
        assert nuevo_comp.responsable == comp.responsable
        assert nuevo_comp.condicion_fiscal == comp.condicion_fiscal
        assert nuevo_comp.total_facturado == Decimal(400).quantize(Decimal(10)**-2)
        assert nuevo_comp.tipo_comprobante == TipoComprobante.objects.get(pk = ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO_ELECTRONICA)
        assert nuevo_comp.nro_terminal == comp.nro_terminal

    def test_crear_comprobante_asociado_falla_si_el_comprobante_no_existe(self):
        with self.assertRaises(Comprobante.DoesNotExist):
            crear_comprobante_asociado(50, Decimal(100), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

    @patch('comprobante.comprobante_asociado.Afip')
    def test_guarda_linea_en_db(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 15

        cantidad_inicial = LineaDeComprobante.objects.count()

        nuevo_comp = crear_comprobante_asociado(1, Decimal(400), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert cantidad_inicial + 1 == LineaDeComprobante.objects.count()
        assert LineaDeComprobante.objects.latest('id').concepto == 'AJUSTA FACTURA {} No {}-{} SEGUN DEBITO APLICADO'.format(nuevo_comp.sub_tipo, nuevo_comp.nro_terminal, nuevo_comp.numero)

        nuevo_comp = crear_comprobante_asociado(1, Decimal(400), 'prueba', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert cantidad_inicial + 2 == LineaDeComprobante.objects.count()
        assert LineaDeComprobante.objects.latest('id').concepto == 'prueba'

    @patch('comprobante.comprobante_asociado.Afip')
    def test_no_guarda_linea_en_db_si_comprobante_falla(self, afip_mock):
        afip = afip_mock()
        afip.emitir_comprobante.side_effect = AfipErrorValidacion

        cantidad_inicial = LineaDeComprobante.objects.count()

        with self.assertRaises(AfipErrorValidacion):
            crear_comprobante_asociado(1, Decimal(199), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        
        assert cantidad_inicial == LineaDeComprobante.objects.count()
        
        afip.emitir_comprobante.side_effect = AfipErrorRed

        with self.assertRaises(AfipErrorRed):
            crear_comprobante_asociado(1, Decimal(100), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert cantidad_inicial == LineaDeComprobante.objects.count()

    @patch('comprobante.comprobante_asociado.Afip')
    def test_crear_comprobante_asociado_falla_si_no_se_realiza_la_conexion_con_afip(self, afip_mock):
        afip_mock.side_effect = AfipErrorRed

        with self.assertRaises(AfipErrorRed):
            crear_comprobante_asociado(1, Decimal(100), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

    @patch('comprobante.comprobante_asociado.Afip')
    def test_crear_comprobante_asociado_falla_si_afip_no_valida_el_comprobante(self, afip_mock):
        afip = afip_mock()

        afip.emitir_comprobante.side_effect = AfipErrorValidacion

        with self.assertRaises(AfipErrorValidacion):
            crear_comprobante_asociado(1, Decimal(100), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

    @patch('comprobante.comprobante_asociado.Afip')
    def test_comprobante_no_se_guarda_en_bd_si_afip_devuelve_error(self, afip_mock):
        afip = afip_mock()

        afip.emitir_comprobante.side_effect = AfipErrorValidacion
        
        cantidad_inicial = Comprobante.objects.count()

        with self.assertRaises(AfipErrorValidacion):
            crear_comprobante_asociado(1, Decimal(199), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)
        
        assert cantidad_inicial == Comprobante.objects.count()
        
        afip.emitir_comprobante.side_effect = AfipErrorRed

        with self.assertRaises(AfipErrorRed):
            crear_comprobante_asociado(1, Decimal(100), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert cantidad_inicial == Comprobante.objects.count()

    @patch('comprobante.comprobante_asociado.Afip')
    def test_guarda_decimales_en_comprobante(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 11

        nuevo_comp = crear_comprobante_asociado(1, Decimal(200.52), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert nuevo_comp.total_facturado == Decimal(200.52).quantize(Decimal(10)**-2)
    
    @patch('comprobante.comprobante_asociado.Afip')
    def test_comprobante_asociado_acepta_iva(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 11

        gravado = Gravado.objects.get(pk=1)
        importe = Decimal('100.21')

        nuevo_comp = crear_comprobante_asociado(1, importe, '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO, gravado.id)
        importe_total = importe + calcular_iva(importe, gravado.porcentaje)
        
        assert nuevo_comp.total_facturado == importe_total.quantize(Decimal(10) ** -2)
        assert nuevo_comp.gravado == gravado

        afip.consultar_proximo_numero.return_value = 12
        gravado = Gravado.objects.get(pk=2)

        nuevo_comp = crear_comprobante_asociado(1, importe, '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO, gravado.id)
        importe_total = importe + calcular_iva(importe, gravado.porcentaje)

        assert nuevo_comp.total_facturado == importe_total.quantize(Decimal(10) ** -2)
        assert nuevo_comp.gravado == gravado

    @patch('comprobante.comprobante_asociado.Afip')
    def test_comprobante_asociado_permite_crear_distintos_tipos(self, afip_mock):
        afip = afip_mock()
        afip.consultar_proximo_numero.return_value = 11

        assert Comprobante.objects.get(pk=1).tipo_comprobante.id == ID_TIPO_COMPROBANTE_FACTURA 

        nuevo_comp = crear_comprobante_asociado(1, Decimal(1), '', ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO)

        assert nuevo_comp.tipo_comprobante.id == ID_TIPO_COMPROBANTE_NOTA_DE_CREDITO

        afip.consultar_proximo_numero.return_value = 11

        nuevo_comp = crear_comprobante_asociado(1, Decimal(1), '', ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO)

        assert nuevo_comp.tipo_comprobante.id == ID_TIPO_COMPROBANTE_NOTA_DE_DEBITO

