# -*- coding: utf-8
from django.http import HttpResponse

import zipfile
import StringIO

from imprimir import generar_factura, obtener_comprobante, obtener_filename
from informe_ventas import obtener_comprobantes_ventas, obtener_archivo_ventas

def imprimir(request, cae):
    # Adquiere datos
    comp = obtener_comprobante(cae)

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = u'filename="{0}.pdf"'.format(obtener_filename(comp['responsable'], comp['cabecera']))

    return generar_factura(response, comp)


# Create your views here.
def ventas(request, responsable, anio, mes):
    # Adquiere datos
    comprobantes = obtener_comprobantes_ventas(responsable, anio, mes)

    # Genera el archivo
    (ventas, alicuotas) = obtener_archivo_ventas(comprobantes)

    # Abre un StringIO para guardar el contenido del archivo
    stream = StringIO.StringIO()

    # Compresor zip
    zipcomp = zipfile.ZipFile(stream, 'w')

    # Agrega los archivos
    zipcomp.writestr(u'VENTAS.txt', u'\r\n'.join(ventas).encode('ascii', 'replace'))
    zipcomp.writestr(u'ALICUOTAS.txt', u'\r\n'.join(alicuotas).encode('ascii', 'replace'))

    # Cierra el archivo y escribe el contenido
    zipcomp.close()

    # Genera el response adecuado
    resp = HttpResponse(stream.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename={0}_{1}_{2}.zip'.format(responsable, anio, mes)

    return resp
