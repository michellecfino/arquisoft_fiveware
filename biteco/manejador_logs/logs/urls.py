from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.py),
    path('', include('logs.urls')),
]
