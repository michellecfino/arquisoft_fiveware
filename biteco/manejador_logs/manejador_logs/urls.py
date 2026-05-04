from django.urls import path
import views

urlpatterns = [
    path("log/", registrar_log),
    path("view/", listar_logs), 
]
