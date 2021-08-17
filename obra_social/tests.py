# -*- coding: utf-8 -*-
import json
from rest_framework import status

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User

from estudio.models import Estudio, Medicacion, ID_SUCURSAL_CEDIR
from obra_social.models import ArancelObraSocial, ObraSocial

class TestDetallesObrasSociales(TestCase):
    fixtures = ['pacientes.json', 'medicos.json', 'practicas.json', 'obras_sociales.json',
                'anestesistas.json', 'presentaciones.json', 'comprobantes.json', 'estudios.json', 'medicamentos.json']

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', is_superuser=True)
        self.client = Client(HTTP_GET='localhost')
        self.client.login(username='test', password='test')

    def test_estudios_sin_presentar_trae_estudios_sin_presentar(self):
        estudio = Estudio.objects.get(pk=12)
        assert estudio.presentacion_id == 0
        assert estudio.obra_social.pk == 1

        response = self.client.get('/api/obra_social/1/estudios_sin_presentar/?sucursal={}'.format(ID_SUCURSAL_CEDIR), content_type='application/json')

        assert response.status_code == status.HTTP_200_OK
        content = json.loads(response.content)
        assert any([e["id"] == 12 for e in content['estudios']])

    def test_estudios_sin_presentar_sugiere_importes(self):
        estudio = Estudio.objects.get(pk=12)
        arancel = ArancelObraSocial.objects.get(obra_social=1, practica=1)
        medicacion = Medicacion.objects.get(pk=3)
        mat_esp = Medicacion.objects.get(pk=4)
        assert estudio.presentacion_id == 0
        assert estudio.obra_social.pk == 1
        assert estudio.practica.pk == 1

        assert medicacion.estudio.id == 12
        assert medicacion.medicamento.tipo == 'Medicaci\xf3n'
        assert medicacion.importe == 1
        assert mat_esp.estudio.id == 12
        assert mat_esp.medicamento.tipo == "Mat Esp"
        assert mat_esp.importe == 1
        assert len(estudio.estudioXmedicamento.all()) == 2

        response = self.client.get('/api/obra_social/1/estudios_sin_presentar/?sucursal={}'.format(ID_SUCURSAL_CEDIR), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK

        estudio_response = [e for e in json.loads(response.content)['estudios'] if e["id"] == 12][0]
        estudio_response["importe_estudio"] == arancel.precio
        estudio_response["importe_medicacion"] == 2

    def test_estudios_sin_presentar_falla_obra_social_invalida(self):
        response = self.client.get('/api/obra_social/-1/estudios_sin_presentar/?sucursal={}'.format(ID_SUCURSAL_CEDIR), content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_estudios_sin_presentar_envia_observaciones(self):
        observaciones = ObraSocial.objects.get(pk=1).observaciones
        response = self.client.get('/api/obra_social/1/estudios_sin_presentar/?sucursal={}'.format(ID_SUCURSAL_CEDIR), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK

        content = json.loads(response.content)
        assert observaciones == content['observaciones']
