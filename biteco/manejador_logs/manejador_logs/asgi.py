import os
from django.core.wsgi import get_wsgi_application

# Cambiamos "manejador_reportes.settings" por "manejador_logs.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manejador_logs.settings")

application = get_wsgi_application()
