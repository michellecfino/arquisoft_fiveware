from django.urls import path
from . import views

urlpatterns = [
    path("registrar/", views.agregar_registro, name="agregar_registro"),
    path("resumen/<int:id_proyecto>/<int:anio>/<int:mes>/", views.consultar_resumen, name="consultar_resumen"),
]