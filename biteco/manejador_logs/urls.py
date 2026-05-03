from django.urls import path
from .views import registrar_log

urlpatterns = [
    path("audit/log/", registrar_log),
]