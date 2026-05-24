from django.contrib import admin
from .models import ResumenMensualCosto, DetalleServicio

@admin.register(ResumenMensualCosto)
class ResumenMensualCostoAdmin(admin.ModelAdmin):
    list_display = ['id_resumen', 'id_empresa', 'id_area', 'id_proyecto', 'anio', 'mes', 'costo_total', 'cantidad_registros']
    list_filter = ['anio', 'mes', 'moneda']
    search_fields = ['id_proyecto', 'id_empresa']
    readonly_fields = ['ultima_actualizacion']

@admin.register(DetalleServicio)
class DetalleServicioAdmin(admin.ModelAdmin):
    list_display = ['id_detalle', 'id_resumen', 'nombre_servicio', 'costo_total', 'cantidad_registros', 'moneda']
    list_filter = ['moneda']
    search_fields = ['nombre_servicio']
    readonly_fields = ['ultima_actualizacion']