"""
urls.py — Configuración de rutas URL de la aplicación Django.
"""

from django.urls import path
from .views import ProjectReportView, HealthCheckView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Endpoint principal del ASR: obtiene el reporte de un proyecto
    # Táctica 3 (Degradation) actúa aquí si la DB no está disponible
    path(
        "api/reports/",
        ProjectReportView.as_view(),
        name="project-report-default",
    ),
    path(
        "api/reports/<int:project_id>/",
        ProjectReportView.as_view(),
        name="project-report",
    ),

    # Health check: expone el estado del Heartbeat (Táctica 1)
    # Usado por load balancers y el Thread Group 3 de JMeter
    path(   
        "health/",
        HealthCheckView.as_view(),
        name="health-check",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

