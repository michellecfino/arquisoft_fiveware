import os
from django.core.asgi import get_asgi_application

# Ajuste crucial para la independencia del microservicio
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manejador_logs.settings")

application = get_asgi_application()
