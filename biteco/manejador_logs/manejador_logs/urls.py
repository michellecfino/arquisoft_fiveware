from django.urls import path, include

urlpatterns = [
    path('', include('logs.urls')),
]
