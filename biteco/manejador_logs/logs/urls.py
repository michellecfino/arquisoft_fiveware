from django.urls import path
from . import views

urlpatterns = [
    path('audit/log/', views.registrar_log),
    path('audit/logs/', views.listar_logs),
]
