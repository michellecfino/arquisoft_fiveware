from django.urls import path
from . import views

urlpatterns = [
    path('ingest/', views.recibir_consumo, name='recibir_consumo'),
    path('resumenes/', views.consultar_resumenes, name='consultar_resumenes'),
    path('dashboard/metricas/', views.obtener_metricas_dashboard, name='metricas_dashboard'),
    path('health/', views.health_check, name='health_check'),
]