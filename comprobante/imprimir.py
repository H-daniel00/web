# -*- coding: utf-8
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import Image
from reportlab.lib.colors import black,white, Color
from reportlab.platypus import Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from qrcode import make as make_qr
from base64 import urlsafe_b64encode

from comprobante.models import *

from textwrap import wrap

from datetime import timedelta

from settings import CEDIR_CUIT, BRUNETTI_CUIT, PROJECT_ROOT

width, height = A4
margin = 6*mm
font_std = 'Helvetica'
font_bld = 'Helvetica-Bold'
max_char = 24

LOGO_AFIP = PROJECT_ROOT + '/static/templates/images/comprobante/logo_afip.png'

mensajes = {
    'mensaje_leyenda_honorarios': 'Este comprobante contiene honorarios por cuenta y órden de médicos.',
    'mensaje_monotributistas': ('El credito fiscal discriminado en el presente comprobante solo ',
                                'podra ser computado a efectos del regimen de sostenimiento ',
                                'e inclusion para pequeños contribuyentes de la ley N° 27.618'),
    'mensaje_legal_factura_electronica': ('Pasados 30 días corridos de recibida sin \n'
                        'haberse producido el rechazo total, aceptación\n'
                        'o pago de esta FACTURA DE CREDITO\n'
                        'ELECTRONICA, se considerará que la misma\n'
                        'constituye título ejecutivo, en los términos del\n'
                        'artículo 523 del Código Procesal, Civil y\n'
                        'Comercial de la Nación y concordantes.\n'
                        'La aceptación expresa o tácita implicará la\n'
                        'plena conformidad para la transferencia de la\n'
                        'información contenida en el documento a\n'
                        'terceros, en caso de optar por su cesión,\n'
                        'transmisión o negociación.')
}

# TODO pasar a base de datos
responsables = {
    'cedir': {
        'CBU': '0150506102000109564632',
        'CUIT': '30709300152',
        'nombre': 'CENTRO DE ENDOSCOPIA DIGESTIVA DE ROSARIO S.A.S.',
        'razon': 'Centro de Endoscopia Digestiva de Rosario S.A.S.',
        'direccion': 'Bv. Oroño 1564. - Rosario Sud, Santa Fe.',
        'condicion_iva': 'IVA Responsable Inscripto',
        'condicion_ib': '021-335420-4',
        'inicio_actividades': '30/06/2005',
    },
    'brunetti': {
        'CUIT': '20118070659',
        'nombre': 'Brunetti Jose Edgar Alberto',
        'razon': 'Brunetti Jose Edgar Alberto',
        'direccion': 'Bv. Oroño 1564. - Rosario Sud, Santa Fe.',
        'condicion_iva': 'IVA Responsable Inscripto',
        'condicion_ib': 'Excento',
        'inicio_actividades': '02/01/1992',
        'mensaje': '"MÉDICO GASTROENTERÓLOGO Mat. Nro. 9314"',
    }
}

def leyenda_monotributista(canvas, mensaje):
    top = height - 243*mm
    box_width = width / 2 + 2*margin
    box_height = 20*mm

    canvas.saveState()
    canvas.rect(margin, top, box_width, box_height, stroke=1, fill=0)
    canvas.setFont(font_std, 11)

    for line, i in zip(mensaje, list(range(len(mensaje)))):
        canvas.drawString(margin * 2, top - margin - i*15 + box_height, line)

    canvas.restoreState()

def codigo_qr(canvas, cabecera):
    size_qr = 35*mm
    posicion_qr = (1.5*margin, 7*mm)
    posicion_afip = (posicion_qr[0]+40*mm, -40*mm)

    qr = make_qr(cabecera["url_qr"])
    canvas.drawInlineImage(qr, posicion_qr[0], posicion_qr[1], width=size_qr, height=size_qr)

    canvas.drawImage(cabecera['logo_afip'], posicion_afip[0], posicion_afip[1], width=size_qr*1.1, preserveAspectRatio=True, mask='auto')

    canvas.setFont(font_bld, 10)
    canvas.drawString(posicion_qr[0] + size_qr + 5*mm, posicion_qr[1] + 15*mm, 'Comprobante Autorizado')

    canvas.saveState()
    canvas.restoreState()


def cae_y_fecha (p, cabecera):
    x, y = width - 40*mm, 30*mm
    p.saveState()
    p.setFont(font_bld, 10)
    p.drawRightString(x, y, 'CAE:')
    p.drawRightString(x, y - 10, 'Fecha de Vto. de CAE:')
    p.setFont(font_std, 10)
    p.drawString(x + 10, y, cabecera['CAE'])
    p.drawString(x + 10, y - 10, cabecera['CAE_vencimiento'])
    p.restoreState()


def encabezado(p, tipo):
    top = margin
    ew = width - 2*margin
    eh = 10*mm
    p.saveState()
    p.rect((width - ew)/2, height - top - eh , ew, eh, stroke=1, fill=0)
    p.setFont(font_bld, 14)
    p.drawCentredString(width/2, height - top - eh/2 - 6, tipo.upper())
    p.restoreState()


def zona_izquierda(p, responsable):
    top = margin + 10*mm
    ew = (width - 2*margin) / 2
    eh = 50*mm
    th = 9
    ld = 25

    p.saveState()
    p.rect(margin, height - top - eh , ew, eh, stroke=1, fill=0)

    t = p.beginText(1.5*margin, height - top - 25)

    # Nombre Grande
    t.setFont(font_bld, 16)
    t.textLines('\n'.join(wrap(responsable['nombre'].upper(), 25)))

    # Nombre
    t.setFont(font_bld, th)
    t.textOut('Razón Social: ')
    t.setFont(font_std, th)
    t.setLeading(ld)
    t.textLine(responsable['razon'])

    # Domicilio
    t.setFont(font_bld, th)
    t.textOut('Domicilio Comercial: ')
    t.setFont(font_std, th)
    t.setLeading(ld)
    t.textLine(responsable['direccion'])

    # Condición IVA
    t.setFont(font_bld, th)
    t.textOut('Condición frente al IVA: ')
    t.setFont(font_std, th)
    t.setLeading(ld)
    t.textLine(responsable['condicion_iva'])

    p.drawText(t)

    p.restoreState()


def zona_derecha(p, cabecera, responsable):
    top = margin + 10*mm
    ew = (width - 2*margin) / 2
    eh = 50*mm
    th = 9
    ld = 28
    fc = 0.45
    sp = 20

    p.saveState()
    p.rect(width - ew - margin, height - top - eh , ew, eh, stroke=1, fill=0)

    t = p.beginText(width - ew - margin + 17*mm, height - top - 25)

    # Descripción factura
    t.setFont(font_bld, 16)

    for s in cabecera['tipo'].split('\n'):
        t.textLine(s.upper())

    # Punto y Numero
    t.setFont(font_bld, th)
    t.setLeading(fc*ld)
    t.textLine('Punto de Venta: {punto_venta:04d}    Comp.Nro: {numero:08d}'.format(**cabecera))

    # Fecha de emisión
    t.textOut('Fecha de Emisión: ')
    t.setFont(font_std, th)
    t.setLeading(sp)
    t.textLine(cabecera['fecha'])

    # CBU
    if cabecera['id_tipo_comprobante'] == ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA:
        t.setFont(font_bld, th)
        t.textOut('CBU: ')
        t.setFont(font_std, th)
        t.setLeading(fc*ld)
        t.textLine(responsable['CBU'])

    # CUIT
    t.setFont(font_bld, th)
    t.textOut('CUIT: ')
    t.setFont(font_std, th)
    t.setLeading(fc*ld)
    t.textLine(responsable['CUIT'])

    # Ingresos Brutos
    t.setFont(font_bld, th)
    t.textOut('Ingresos Brutos: ')
    t.setFont(font_std, th)
    t.setLeading(fc*ld)
    t.textLine(responsable['condicion_ib'])

    # Inicio de actividades
    t.setFont(font_bld, th)
    t.textOut('Inicio de Actividades: ')
    t.setFont(font_std, th)
    t.setLeading(fc*ld)
    t.textLine(responsable['inicio_actividades'])

    p.drawText(t)
    p.restoreState()


def zona_central(p, cabecera):
    top = margin + 10*mm
    ew = 16*mm
    eh = 13*mm
    p.saveState()
    p.setFillColor(white)
    p.rect((width - ew)/2, height - top - eh , ew, eh, stroke=1, fill=1)
    p.setFillColor(black)
    p.setFont(font_bld, 20)
    p.drawCentredString(width/2, height - top - eh/2, cabecera['letra'])
    p.setFont(font_bld, 10)
    p.drawCentredString(width/2, height - top - eh + 7, 'COD.' + cabecera['codigo'])
    p.restoreState()


def post_encabezado(p, cabecera):
    top = margin + 60*mm
    ew = width - 2*margin
    eh = 8*mm
    th = 10

    p.saveState()
    p.rect((width - ew)/2, height - top - eh , ew, eh, stroke=1, fill=0)

    t = p.beginText(margin + 17*mm, height - top - 15)

    # Período desde
    t.setFont(font_bld, th)
    t.textOut('Período Facturado Desde: ')
    t.setFont(font_std, th)
    t.textOut(cabecera['desde'])

    # ... hasta
    t.setFont(font_bld, th)
    t.textOut('    Hasta: ')
    t.setFont(font_std, th)
    t.textOut(cabecera['hasta'])

    #
    t.setFont(font_bld, th)
    t.textOut('    Fecha Vencimiento Pago: ')
    t.setFont(font_std, th)
    t.textOut(cabecera['vencimiento'])

    p.drawText(t)

    p.restoreState()


def datos_cliente(p, cliente):
    top = margin + 68*mm
    ew = width - 2*margin
    eh = 25*mm
    th = 10

    p.saveState()
    p.rect((width - ew)/2, height - top - eh , ew, eh, stroke=1, fill=0)

    t = p.beginText(1.5*margin, height - top - 15)

    # Razón Social
    t.setFont(font_bld, th)
    t.textOut('Apellido y Nombre / Razón Social: ')
    t.setFont(font_std, th)
    t.textLine(cliente['nombre'])

    # Domicilio
    t.setFont(font_bld, th)
    t.textOut('Domicilio Comercial: ')
    t.setFont(font_std, th)
    t.textLine(cliente['direccion'])

    # CUIT
    t.setFont(font_bld, th)
    t.textOut('CUIT: ' if len(cliente['CUIT']) > 10 else 'DNI: ')
    t.setFont(font_std, th)
    t.textLine(cliente['CUIT'])

    # Condición frente al IVA
    t.setFont(font_bld, th)
    t.textOut('Condición frente al IVA: ')
    t.setFont(font_std, th)
    t.textLine(cliente['condicion_iva'])

    # Condición de venta
    t.setFont(font_bld, th)
    t.textOut('Condición de venta: ')
    t.setFont(font_std, th)
    t.textLine(cliente['condicion_venta'])

    p.drawText(t)

    p.restoreState()


def detalle_lineas(p, header, sizes, lineas):
    tw = width - 2*margin
    table = Table(header + lineas, colWidths=[size * tw for size in sizes])
    table.setStyle([
        ('FONT', (0, 0), (-1, -1), font_std),
        ('FONT', (0, 0), (-1, 0), font_bld),
        ('LEADING', (0, 1), (-1, -1), 5),
        ('GRID', (0, 0), (-1, 0), 0.5, black),
        ('BACKGROUND', (0, 0), (-1, 0), Color(0.8,0.8,0.8)),
        ('ALIGN', (1, 0), (-1, -1), 'CENTRE'),
        ('ALIGN', (1, 1), (-3, -1), 'RIGHT'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ])
    mw, mh = table.wrapOn(p, width, height)
    table.drawOn(p, margin, height - 99*mm - mh)

def imprimir_mensaje(p, cabecera):

    if cabecera['id_tipo_comprobante'] != ID_TIPO_COMPROBANTE_FACTURA_CREDITO_ELECTRONICA:
        return

    mensaje = mensajes['mensaje_legal_factura_electronica'].split('\n')

    top = 170*mm
    ew = (width - 2*margin) / 2
    eh = 72*mm 
    y_pos = height - top - eh - 2

    p.saveState()
    p.rect( margin, y_pos , ew, eh, stroke=1, fill=0)
    p.setFont(font_std, 12)

    for line, i in zip(mensaje, list(range(len(mensaje)))):
        p.drawString(margin * 2, y_pos + eh - margin - i*15 - 5, line)

    p.restoreState()


def detalle_iva(p, detalle):
    table = Table(detalle, [5*cm, 3*cm])
    table.setStyle([
        ('FONT', (0, 0), (-1, -1), font_bld),
        ('LEADING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ])
    table.wrapOn(p, width, height)
    table.drawOn(p, width - margin - 8*cm, 55*mm)


def pie_de_pagina(p, imprimir_leyenda_honorarios):
    mensaje = mensajes['mensaje_leyenda_honorarios'] if imprimir_leyenda_honorarios else ''
    top = 245*mm
    ew = width - 2*margin
    eh = 7*mm if mensaje else 0

    p.saveState()
    p.rect((width - ew)/2, height - top - eh - 3 , ew, eh, stroke=1, fill=0)
    p.setFont(font_std, 12)
    p.drawCentredString(width/2, height - top - eh/2 - 6, mensaje)
    p.restoreState()


def generar_factura(response, comp, leyenda):
    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response, pagesize=A4)
    p.setTitle(obtener_filename(comp['responsable'], comp['cabecera']))

    for copia in ['Original', 'Duplicado', 'Triplicado']:

        p.setLineWidth(0.5)

        # Escribe encabezado
        encabezado(p, copia)

        zona_izquierda(p, comp['responsable'])

        zona_derecha(p, comp['cabecera'], comp['responsable'])

        zona_central(p, comp['cabecera'])

        post_encabezado(p, comp['cabecera'])

        datos_cliente(p, comp['cliente'])

        detalle_lineas(p, comp['headers'], comp['sizes'], comp['lineas'])

        imprimir_mensaje(p, comp['cabecera'])

        detalle_iva(p, comp['detalle'])

        pie_de_pagina(p, mensajes['mensaje_leyenda_honorarios'])

        leyenda_monotributista(p, mensajes['mensaje_monotributistas'])

        # Escribe código de qr
        codigo_qr(p, comp['cabecera'])

        # Escribe el CAE y la fecha
        cae_y_fecha(p, comp['cabecera'])

        # Close the PDF object cleanly, and we're done.
        p.showPage()

    p.save()
    return response


def obtener_codigo_barras(c):
    r = responsables[c.responsable.lower()]
    x = '{0}{1:02d}{2:04d}{3}{4}'.format(
        r['CUIT'].replace('-', ''),
        c.codigo_afip,
        c.nro_terminal,
        c.cae,
        c.vencimiento_cae.strftime('%Y%m%d')
        )
    return int(x)


def format_gravado_linea(grav):
    return '{0}%'.format(grav.porcentaje) if grav.porcentaje else grav.descripcion


def format_gravado_detalle(grav):
    return 'Importe Neto Gravado: $' if grav.porcentaje else 'Importe Excento: $'


def obtener_subtotal_comprobante(c):
    return '{0:.2f}'.format(c.importe_gravado_afip)


def obtener_iva_comprobante(c, iva):
    return c.importe_alicuota_afip if c.gravado.porcentaje == iva else 0.0


def obtener_lineas_comprobante(c):
    styles = styles=getSampleStyleSheet()
    if c.sub_tipo.upper() == 'A':
        return [[Paragraph(l.concepto.replace('\r','').replace('\n','<br/>'), styles["Normal"]), '{0:.2f}'.format(l.importe_neto), format_gravado_linea(c.gravado), '{0:.2f}'.format(l.sub_total)] for l in c.lineas.all()]
    else:
        return [[Paragraph(l.concepto.replace('\r','').replace('\n','<br/>'), styles["Normal"]), '{0:.2f}'.format(l.sub_total)] for l in c.lineas.all()]


def obtener_headers_lineas(c):
    if c.sub_tipo.upper() == 'A':
        return [['Producto / Servicio', 'Subtotal', 'Alícuota IVA', 'Subtotal c/IVA']]
    else:
        return [['Producto / Servicio', 'Subtotal']]


def obtener_headers_sizes(c):
    if c.sub_tipo.upper() == 'A':
        return [0.6, 0.14, 0.12, 0.14]
    else:
        return [0.86, 0.14]


def obtener_detalle_iva(c):
    ivas = [27, 21, 10.5, 5, 2.5, 0]
    if c.sub_tipo.upper() == 'A':
        result = [
            [format_gravado_detalle(c.gravado), obtener_subtotal_comprobante(c)],
            ['', '']
        ]

        result += [
            ['IVA {0}%: $'.format(iva), '{0:.2f}'.format(obtener_iva_comprobante(c, iva))]
            for iva in ivas
            ]
    else:
        result = [
            ['Subtotal: $', '{0:.2f}'.format(c.total_facturado)],
            ['', '']
        ]

        result += [['', ''] for _ in ivas]

    result += [
        ['Importe Otros Tributos: $', '0.00'],
        ['Importe Total: $', '{0:.2f}'.format(c.total_facturado)],
    ]
    return result

def format_tipo_comprobante(nombre):

    if len(nombre) <= max_char:
        return nombre
    
    result = ''
    amount_chars = 0
    
    for word in nombre.split(' '):
        amount_chars += len(word)
        if amount_chars > max_char:
            result += '\n'
            amount_chars = 0
        result += word + ' '
    
    return result

def obtener_comprobante(cae):
    c = Comprobante.objects.get(cae=cae)

    return {
        'cabecera': {
            'codigo': '{0:02d}'.format(c.codigo_afip),
            'tipo': format_tipo_comprobante(c.tipo_comprobante.nombre),
            'id_tipo_comprobante': c.tipo_comprobante.id,
            'letra': c.sub_tipo,
            'punto_venta': c.nro_terminal,
            'numero': c.numero,
            'fecha': c.fecha_emision.strftime('%d/%m/%Y'),
            'desde': '  /  /    ',
            'hasta': '  /  /    ',
            'vencimiento': (c.fecha_vencimiento).strftime('%d/%m/%Y'),
            'CAE': c.cae,
            'CAE_vencimiento': c.vencimiento_cae.strftime('%d/%m/%Y'),
            'url_qr': 'https://www.afip.gob.ar/fe/qr/?p=' + urlsafe_b64encode(bytes(str({ # Datos necesarios de la afip para generar el qr
                'ver': 1,                                                                 # https://www.afip.gob.ar/fe/qr/especificaciones.asp
                'fecha': c.fecha_emision.strftime("%Y-%m-%d"),
                'cuit': CEDIR_CUIT if c.responsable == 'Cedir' else BRUNETTI_CUIT,
                'ptoVta': c.nro_terminal,
                'tipoCmp': c.codigo_afip,
                'nroCmp': c.numero,
                'importe': float(c.total_facturado),
                'moneda': 'PES',
                'ctz': 1,
                'tipoCodAut': 'E',
                'codAut': int(c.cae),
            }), 'utf-8')).decode('utf-8'),
            'logo_afip': LOGO_AFIP,
        },
        'cliente': {
            'CUIT': c.nro_cuit,
            'nombre': c.nombre_cliente,
            'condicion_iva': c.condicion_fiscal,
            'condicion_venta': 'Otra',
            'direccion': c.domicilio_cliente,
        },
        'responsable': responsables[c.responsable.lower()],
        'headers': obtener_headers_lineas(c),
        'sizes': obtener_headers_sizes(c),
        'lineas': obtener_lineas_comprobante(c),
        'detalle': obtener_detalle_iva(c)
    }


def obtener_filename(responsable, encabezado):
    return '{0}_{1}_{2:04d}_{3:08d}'.format(
        responsable['CUIT'],
        encabezado['codigo'],
        encabezado['punto_venta'],
        encabezado['numero'],
        )
