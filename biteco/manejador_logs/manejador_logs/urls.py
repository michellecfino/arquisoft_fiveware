# ~/arquisoft_fiveware/biteco/manejador_logs/manejador_logs/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('logs.urls')),
]
