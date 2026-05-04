from django.urls import path
from . import views  # Importación relativa correcta

urlpatterns = [
    path('audit/log/', views.registrar_log, name='registrar_log'),
]
