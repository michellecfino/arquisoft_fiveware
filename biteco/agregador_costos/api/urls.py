from django.urls import path
from . import views

urlpatterns = [
    path('ingest/', views.ingest, name='ingest'),
    path('resumenes/', views.resumenes_list, name='resumenes'),
    path('health/', views.health, name='health'),
]
