from datetime import date
from comprobante.models import Comprobante, TipoComprobante, LineaDeComprobante, Gravado
from comprobante.afip import Afip, AfipError, AfipErrorRed, AfipErrorValidacion
from decimal import Decimal

from comprobante.models import ID_TIPO_COMPROBANTE_LIQUIDACION

class TipoComprobanteAsociadoNoValidoException(Exception):
    pass

def calcular_iva(importe, porcentaje):
    iva = importe * porcentaje / 100
    return iva.quantize(Decimal(10) ** -2)

def _crear_comprobante_similar(comp, importe, id_tipo_comp, numero, gravado):
    iva = calcular_iva(importe, gravado.porcentaje)
    return Comprobante(**{
        'nombre_cliente' : comp.nombre_cliente,
        'domicilio_cliente': comp.domicilio_cliente,
        'nro_cuit': comp.nro_cuit,
        'gravado_paciente': comp.gravado_paciente,
        'condicion_fiscal': comp.condicion_fiscal,
        'responsable': comp.responsable,
        'sub_tipo': comp.sub_tipo,
        'estado': Comprobante.COBRADO,
        'numero': numero,
        'nro_terminal': comp.nro_terminal,
        'total_facturado': importe + iva,
        'total_cobrado': importe + iva,
        'fecha_emision': date.today(),
        'fecha_recepcion': date.today(),
        'tipo_comprobante': TipoComprobante.objects.get(pk = id_tipo_comp),
        'factura': comp,
        'gravado': gravado,
    })

def _crear_linea(comp, importe, concepto, gravado):
    iva = calcular_iva(importe, gravado.porcentaje)
    return [LineaDeComprobante(**{
        'comprobante': comp,
        'concepto': concepto if concepto != '' else 'AJUSTA FACTURA {} No {}-{} SEGUN DEBITO APLICADO'.format(comp.sub_tipo, comp.nro_terminal, comp.numero),
        'importe_neto': importe,
        'sub_total': importe + iva,
        'iva': iva,
    })]


def crear_comprobante_asociado(id_comp, importe, concepto, tipo_comprobante, tipo_iva = None):
    importe = importe.quantize(Decimal(10) ** -2)

    comp = Comprobante.objects.get(pk = id_comp)

    gravado = Gravado.objects.get(pk=tipo_iva) if tipo_iva else comp.gravado

    if comp.tipo_comprobante.id == ID_TIPO_COMPROBANTE_LIQUIDACION:
        raise TipoComprobanteAsociadoNoValidoException("No es posible usar una liquidacion como comprobante asociado")

    afip = Afip()

    nro_siguiente = afip.consultar_proximo_numero(
        comp.responsable,
        comp.nro_terminal,
        TipoComprobante.objects.get(pk = tipo_comprobante),
        comp.sub_tipo
    )

    comprobante = _crear_comprobante_similar(comp, importe, tipo_comprobante, nro_siguiente, gravado)

    lineas = _crear_linea(comprobante, importe, concepto, gravado)

    afip.emitir_comprobante(comprobante, lineas)

    comprobante.save()

    lineas[0].comprobante = Comprobante.objects.get(pk=comprobante.id)

    lineas[0].save()

    return comprobante