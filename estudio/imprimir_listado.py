from caja.imprimir import paragraph, setUpStyles, pdf_tabla, MARGINS
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

styles = setUpStyles()

def generar_pdf_estudio_list(response, estudios):
    pdf = SimpleDocTemplate(
        response,
        pagesize=A4,
        title='Listado de estudios',
        topMargin=MARGINS['top'],
        bottomMargin=MARGINS['bottom'],
    )

    elements = pdf_tabla(estudios, pdf_tabla_encabezado, pdf_tabla_body)

    pdf.build(elements)
    return response

def pdf_tabla_encabezado():
    return [[
        paragraph('Fecha'),
        paragraph('Paciente'),
        # paragraph('Telefono'),
        paragraph('Obra social'),
        paragraph('Practica'),
        paragraph('Estado'),
        paragraph('Medico actuante')
    ]]

def pdf_tabla_body(estudios):
    return [
        [paragraph(estudio[key]) for key in ['fecha', 'paciente', 'obra_social', 'practica', 'estado', 'medico']]
        for estudio in estudios
    ]