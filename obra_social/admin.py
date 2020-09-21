from django.contrib import admin
from .models import ObraSocial, ArancelObraSocial


class ObraSocialAdmin(admin.ModelAdmin):
    actions = None
    search_fields = ['nombre']
    list_display = ('nombre', 'telefono', 'localidad', 'direccion', 'codigo_postal', 'valor_aproximado_pension')

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ObraSocial, ObraSocialAdmin)


class ArancelObraSocialAdmin(admin.ModelAdmin):
    actions = None
    search_fields = ['practica__descripcion', 'obra_social__nombre']
    list_display = ('practica', 'obra_social', 'precio', 'precio_anestesia', 'fecha')

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ArancelObraSocial, ArancelObraSocialAdmin)
