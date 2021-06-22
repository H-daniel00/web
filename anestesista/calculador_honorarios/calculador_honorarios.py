# -*- coding: utf-8 -*-
from decimal import Decimal, ROUND_UP
import ast
import operator as op
from datetime import timedelta
from anestesista.models import Complejidad, ComplejidadEstudio, SIN_ANESTESIA
from comprobante.models import LineaDeComprobante


def eval_expr(expr):
    
    operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
        ast.USub: op.neg}
    def eval_(node):
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return operators[type(node.op)](eval_(node.left), eval_(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return operators[type(node.op)](eval_(node.operand))
        else:
            raise TypeError(node)
    return eval_(ast.parse(expr, mode='eval').body)


TIPO_MOV_CAJA_HONORARIO_ANESTESISTA = 3
TIPO_MOV_CAJA_COSEGURO = 10
PORCENTAJE_DESCUENTO_CEDIR = Decimal('0.35')
SIMARA_ID = 6
SIMARA_IMPORTE_C2 = 'c1'  # c2 = c1 para Simara


class CalculadorHonorariosAnestesista(object):

    def __init__(self, anestesista, estudios, obra_social, *args, **kwargs):
        self.anestesista = anestesista
        self.estudios = estudios
        self.obra_social = obra_social
        self.complejidades = Complejidad.objects.all()  # TODO: ver si esta consulta se puede evitar (cachear) ya que se hace por cada instancia
        self.paciente = self.estudios[0].paciente

    def calculate(self):
        """
        Si la OS se presenta por ARA, se calculan los importes en base a sus reglas de negocio.
        Lo mismo si la OS no se presenta por ARA.
        Pero si la OS se presenta por ARA y a su vez tiene movimientos de caja, entonces se calculan para las dos.
        """
        complejidad = self._get_complejidad_a_aplicar(self.estudios)
        if not complejidad:
            raise Complejidad.DoesNotExist

        formula = complejidad.formula.lower()
        formula_valorizada = self._valorizar_formula(formula)

        importe = Decimal(eval_expr(formula_valorizada))
        importe *= self._get_coeficiente_paciente_diferenciado()
        movimientos_caja = self._get_movimientos_de_caja()
        total_mov_caja = sum([mov.monto for mov in movimientos_caja])
        
        result_ara = {}
        result_no_ara = {}
        if int(self.obra_social.se_presenta_por_ARA):
            result_ara = self._get_importes_ara(importe, total_mov_caja)
            if movimientos_caja:
                result_no_ara = self._get_importes_no_ara(importe, bool(movimientos_caja), total_mov_caja)
        else:
            result_no_ara = self._get_importes_no_ara(importe, bool(movimientos_caja), total_mov_caja)

        return {'movimientos_caja': movimientos_caja, 'total_mov_caja': total_mov_caja, 'formula': formula, 
                'formula_valorizada': formula_valorizada, 'ara': result_ara,  'no_ara': result_no_ara}

    def _valorizar_formula(self, formula):
        """
        Reemplazar variables en la formula (c1 + c2 - 20) por valores sacados de las complejidades.
        """
        formula_valorizada = formula
        if self.obra_social.id == SIMARA_ID:  # esta es una excepcion que pronto se va a sacar. Simara hace c2 = c1
            formula_valorizada = formula_valorizada.replace('c2', SIMARA_IMPORTE_C2)
        for c in self.complejidades:
            formula_valorizada = formula_valorizada.replace('c{0}'.format(c.id), c.importe)
        return formula_valorizada

    def _get_complejidad_a_aplicar(self, estudios):
        """
        # generamos el patron de busqueda para la complejidad
        # (es una lista de codigos de practicas IDs ordenada y separada por coma)
        Para que el filtro de complefidadEstudio funcione, debe estar guardado en forma ascendente
        """
        estudios_id = ','.join([str(practica_id) for practica_id in sorted(set([estudio.practica.id for estudio in estudios]))])
        complejidad = ComplejidadEstudio.objects.filter(estudios=estudios_id).first()
        return complejidad

    def _get_movimientos_de_caja(self):
        movimientos_caja = [mov
            for estudio in self.estudios
            for mov     in estudio.movimientos_caja.filter(tipo_id__in=[TIPO_MOV_CAJA_HONORARIO_ANESTESISTA, TIPO_MOV_CAJA_COSEGURO])
        ]
        return movimientos_caja

    def _get_comprobante_particular(self):
        """
        el comprobante hay que buscarlo usando el DNI del paciente, fechar del comprobante mayor igual a la fecha de estuido y rngo de 30 dias, 
        y buscar palabra anest dentro de la desc del comprobante (factura)
        # Busqueda se realiza case insensitive (icontains)
        """
        startdate = self.estudios[0].fecha
        enddate = startdate + timedelta(days=30)
        lineas = LineaDeComprobante.objects.filter(comprobante__nro_cuit=self.paciente.dni, comprobante__fecha_emision__range=[startdate, enddate], concepto__icontains='anest')
        if bool(lineas):
            return lineas[0].comprobante

    def _get_comprobante_desde_facturacion(self):
        """
        Si no va por ara y es de obra social (no particular) se saca el iva del comprobante asociado a la presentacion.
        """
        estudio = self.estudios[0]
        if estudio.presentacion_id:  # esto puede ser = 0 si no esta facturado
            return estudio.presentacion.comprobante

    def _es_paciente_diferenciado(self):
        """
        Devuelve True si la edad del paciente esta entre 1 y 12, o mayor a 70 anios.
        """
        if self.anestesista.id == SIN_ANESTESIA:
            return False
        return 1 <= self.paciente.get_edad() <=12 or self.paciente.get_edad() >= 70

    def _get_coeficiente_paciente_diferenciado(self):
        """
        Si la edad del paciente esta entre 1 a 12 o mayor a 70, se considera diferenciado.
        En este caso, el coficiente es 1.3 (30% mas). De otro modo es 1 (100%)
        """
        if self._es_paciente_diferenciado():
            return Decimal('1.3')
        return Decimal('1')

    def _get_importes_ara(self, importe, total_mov_caja):
        alicuota_iva = Decimal('21.0')
        importe = importe - total_mov_caja  # total_mov_caja = 0 si no hubiese
        sub_total = importe - (importe * PORCENTAJE_DESCUENTO_CEDIR)
        sub_total = sub_total.quantize(Decimal('.01'), ROUND_UP)
        retencion = sub_total * self.anestesista.porcentaje_anestesista / Decimal(100)

        return {'importe': importe, 'sub_total': sub_total, 'retencion': retencion, 'alicuota_iva': alicuota_iva}

    def _get_importes_no_ara(self, importe, existen_mov_caja, total_mov_caja):
        """
        Retencion aca es 'a pagar'
        """
        comprobante = None
        if int(self.obra_social.se_presenta_por_ARA):
            assert existen_mov_caja == True, 'Deberia haber movimientos si se presenta por ARA y se esta caclulando No ARA'
            importe = total_mov_caja.quantize(Decimal('.01'), ROUND_UP)
            alicuota_iva = Decimal('0.0')  # es cero porque ya esta incluido en el monto del mov. de caja
        else:
            if self.obra_social.is_particular_or_especial():
                comprobante = self._get_comprobante_particular()
            else:
                comprobante = self._get_comprobante_desde_facturacion()
            
            alicuota_iva = Decimal(comprobante.gravado.porcentaje) if comprobante and comprobante.tipo_comprobante.nombre != 'Liquidacion' else Decimal('0.0')
            comprobante = comprobante

        sub_total = importe - (importe * PORCENTAJE_DESCUENTO_CEDIR)
        sub_total = sub_total.quantize(Decimal('.01'), ROUND_UP)
        a_pagar = sub_total * (Decimal(100) - self.anestesista.porcentaje_anestesista) / Decimal(100)
        
        return {'importe': importe, 'sub_total': sub_total, 'a_pagar': a_pagar, 'alicuota_iva': alicuota_iva, 
                'comprobante': comprobante}

