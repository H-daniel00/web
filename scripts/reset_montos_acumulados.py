# Set directory
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# Init Django
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
django.setup()

# Reset MontosAcumulados
from caja.models import MovimientoCaja, MontoAcumulado, ID_CONSULTORIO_1, ID_CONSULTORIO_2, ID_GENERAL

def reset_montos():
    for id in (ID_CONSULTORIO_1, ID_CONSULTORIO_2):
        monto = MontoAcumulado.objects.get(tipo__id=id)
        monto.monto_acumulado = 0
        monto.save()
    
    monto = MontoAcumulado.objects.get(tipo__id=ID_GENERAL)
    monto.monto_acumulado = MovimientoCaja.objects.last().monto_acumulado
    monto.save()

reset_montos()
