# -*- coding: utf-8 -*-
from abc import abstractmethod, abstractproperty
from decimal import Decimal
import decimal
from .porcentajes import Porcentajes
from .descuentos import Descuento, DescuentosVarios, DescuentoColangios, DescuentoStent, DescuentoRadiofrecuencia, \
                       DescuentoPorPolipectomia
from estudio.models import Estudio

class CalculadorHonorarios(object):
    '''
    Clase abstracta.
    Dado un estudio, aplica todas las reglas de negocios correspondientes para calcular los honorarios de los medicos implicados en el mismo.
    Es responsabilidad del heredero de esta clase elegir implementar sus reglas especificas segun en que contexto se esta calculando.
    '''
    def __init__(self, estudio : Estudio):
        self.estudio = estudio
        self.calcular()
        self.porcentajes = Porcentajes(self.estudio)

    @abstractmethod
    def get_importe(self) -> Decimal:
        raise NotImplementedError

    @abstractproperty
    def descuentos(self) -> Descuento:
        raise NotImplementedError

    def porcentaje_GA(self) -> Decimal:
        return self.factor_GA * Decimal('100.00')

    def calcular(self):
        '''
        Logica principal comun para todos los casos.
        Los honorarios de un medico siempre se calculan de la siguiente forma:
        1) Se busca el importe adecuado del estudio y se sacan los gastos administrativos.
        2) Se realizan los descuentos que correspondan.
        3) Se asignan los honorarios de cada medico segun los porcentajes que
          apliquen.
        '''
        importe_estudio = self.get_importe()
        monto_descuentos = self.uso_de_materiales
        r1 = Decimal('1.00') - self.factor_GA
        self.total_honorarios = importe_estudio * r1 - monto_descuentos

    @property
    def actuante(self) -> Decimal:
        return Decimal(self.total_honorarios) * (self.porcentajes.actuante) / Decimal('100.00')

    @property
    def solicitante(self) -> Decimal:
        return Decimal(self.total_honorarios) * (self.porcentajes.solicitante) / Decimal('100.00')

    @property
    def honorarios_medicos(self) -> Decimal:
        return Decimal(self.total_honorarios) * (self.porcentajes.solicitante + self.porcentajes.actuante) / Decimal('100.00')

    @property
    def cedir(self) -> Decimal:
        return Decimal(self.total_honorarios * self.porcentajes.cedir) / Decimal('100.00')

    @property
    def uso_de_materiales(self) -> Decimal:
        return self.descuentos.aplicar(self.estudio, self.get_importe())

    @property
    def factor_GA(self) -> Decimal:
        return self.estudios.retencion_impositiva

class CalculadorHonorariosInformeContadora(CalculadorHonorarios):
    '''
    En el informe de la contadora se utilizan siempre los valores facturados.
    Ademas, no nos interesa saber los honorarios de un medico particular,
    solo el total de honorarios.
    '''
    def get_importe(self) -> Decimal:
        return Decimal(self.estudio.importe_estudio) - Decimal(self.estudio.diferencia_paciente)

    @property
    def descuentos(self) -> Descuento:
        return DescuentosVarios(
            DescuentoPorPolipectomia(),
            DescuentoColangios(),
            DescuentoStent(),
            DescuentoRadiofrecuencia()
        )

class CalculadorHonorariosPagoMedico(CalculadorHonorarios):
    '''
    En el caso de un pago a un medico, las reglas a usar dependeran de como se
    facturo el estudio.
    Si la facturacion la realiza el cedir, se calcula a partir de los valores
    cobrados, cuanto recibe el medico en honorarios.
    Si el estudio es pago contra factura, se calcula cuanto debe pagar el
    medico al cedir.
    '''
    def get_importe(self) -> Decimal:
        estudio = self.estudio
        if estudio.es_pago_contra_factura:
            return Decimal(estudio.pago_contra_factura)
        else:
            return Decimal(estudio.importe_estudio_cobrado)

    @property
    def descuentos(self) -> Descuento:
        # TODO: No esta checkeado
        return DescuentosVarios(
            DescuentoPorPolipectomia(),
            DescuentoColangios(),
            DescuentoStent(),
            DescuentoRadiofrecuencia()
        )

