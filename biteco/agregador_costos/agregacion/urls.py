from django.urls import path
from . import views

urlpatterns = [
    # Endpoint interno para ingesta de datos
    path("internal/ingest/", views.ingest_data, name="ingest_data"),
]