from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("reportes.urls")),
    path("audit/", include("manejador_logs.urls")), 
]
