from django.urls import path
from . import views

urlpatterns = [
    path("<int:id_proyecto>/<int:anio>/<int:mes>/", views.resumen_reporte, name="resumen_reporte"),
]