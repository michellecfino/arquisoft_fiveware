from django.urls import path
from . import views

urlpatterns = [
    path("api/reportes/generar/", views.generar_reporte, name="generar_reporte"),
    path("api/reportes/<int:id_proyecto>/<int:anio>/<int:mes>/", views.resumen_reporte_api, name="resumen_reporte_api"),
    path("reportes/<int:id_proyecto>/<int:anio>/<int:mes>/", views.resumen_reporte_vista, name="resumen_reporte_vista"),
]