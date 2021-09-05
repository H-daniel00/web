# -*- coding: utf-8 -*-
from abc import abstractmethod, abstractproperty
from decimal import Decimal
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

    @abstractmethod
    def get_importe(self) -> Decimal:
        raise NotImplementedError

    @abstractproperty
    def descuentos(self) -> Descuento:
        raise NotImplementedError

    def porcentaje_GA(self) -> Decimal:
        return self.estudio.retencion_impositiva * Decimal('100.00')

    def calcular(self):
        '''
        Logica principal comun para todos los casos.
        Los honorarios de un medico siempre se calculan de la siguiente forma:
        1) Se busca el importe adecuado del estudio y se sacan los gastos administrativos.
        2) Se realizan los descuentos que correspondan.
        3) Se asignan los honorarios de cada medico segun los porcentajes que
          apliquen.
        '''
        porcentaje_GA = self.porcentaje_GA()

        importe_estudio = self.get_importe()
        monto_descuentos = self.uso_de_materiales
        r1 = (Decimal('100.00') - porcentaje_GA) / Decimal('100.00') # Creo que se puede hacer 1 - retencion_impositiva
        self.total_honorarios = importe_estudio * r1 - monto_descuentos

    @property
    def actuante(self) -> Decimal:
        porcentajes = Porcentajes(self.estudio) # Creo que se puede guardar en el init
        # total = Decimal(self.total_honorarios) * (porcentajes.actuante + porcentajes.solicitante) / Decimal('100.00')
        total = Decimal(self.total_honorarios) * (porcentajes.actuante) / Decimal('100.00')
        return total


    @property
    def solicitante(self) -> Decimal:
        porcentajes = Porcentajes(self.estudio)
        total = Decimal(self.total_honorarios) * (porcentajes.solicitante) / Decimal('100.00')
        return total

    @property
    def cedir(self) -> Decimal:
        porcentajes = Porcentajes(self.estudio) # Ver si es posible cambiar todo a proporcion (En vez de 32% usar 0.32)
        return Decimal(self.total_honorarios * porcentajes.cedir) / Decimal('100.00')

    @property
    def uso_de_materiales(self) -> Decimal:
        return self.descuentos.aplicar(self.estudio, self.get_importe())


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

