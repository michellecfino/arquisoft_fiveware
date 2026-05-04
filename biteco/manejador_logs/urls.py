from django.urls import path
from .views import registrar_log, listar_logs

urlpatterns = [
    path("log/", registrar_log),
    path("view/", listar_logs), 
]
