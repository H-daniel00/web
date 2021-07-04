from caja.imprimir import paragraph, setUpStyles, pdf_tabla, MARGINS
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

styles = setUpStyles()

COLUMNAS = (('Fecha', 20*mm, 'fecha'), ('Paciente', 35*mm, 'paciente'),
            ('Telefono', 28*mm, 'telefono'), ('Obra social', 30*mm, 'obra_social'),
            ('Practica', 20*mm, 'practica'), ('Estado', 25*mm, 'estado'),
            ('Medico actuante', 32*mm, 'medico'))

def generar_pdf_estudio_list(response, estudios):
    pdf = SimpleDocTemplate(
        response,
        pagesize=A4,
        title='Listado de estudios',
        topMargin=MARGINS['top'],
        bottomMargin=MARGINS['bottom'],
    )

    largos_columnas = [columna[1] for columna in COLUMNAS]
    elements = pdf_tabla(estudios, largos_columnas, pdf_tabla_encabezado, pdf_tabla_body)

    pdf.build(elements)
    return response

def pdf_tabla_encabezado():
    return [[paragraph(columna[0]) for columna in COLUMNAS]]

def pdf_tabla_body(estudios):
    return [
        [paragraph(estudio[columna[2]]) for columna in COLUMNAS]
        for estudio in estudios
    ]
