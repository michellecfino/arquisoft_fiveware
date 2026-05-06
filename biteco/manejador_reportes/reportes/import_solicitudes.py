# import_solicitudes.py
import csv
import os
import django
from django.utils import timezone

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manejador_reportes.settings")
django.setup()

# Importar modelos
from reportes.models import ReporteGenerado
from nucleo.models import Proyecto, Usuario

# Ruta de tu CSV
CSV_PATH = os.path.expanduser('~/arquisoft_fiveware/biteco/jmeter/data/solicitudes_20000.csv')

# Obtener un usuario de prueba
usuario = Usuario.objects.first()  # Ajusta si quieres un usuario específico

# Contador para generar request_id único
counter = 1

with open(CSV_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            proyecto = Proyecto.objects.get(pk=int(row['id_proyecto']))
            ReporteGenerado.objects.create(
                id_empresa=proyecto.id_empresa,
                id_area=proyecto.id_area,
                id_proyecto=proyecto.id_proyecto,
                id_usuario=usuario.id_usuario,
                anio=int(row['anio']),
                mes=int(row['mes']),
                moneda='COP',  # o 'USD', según prefieras
                total_costo=0,
                cantidad_registros=0,
                request_id=f'test-{counter}',
                instancia_origen='manejador_reportes',
                fecha_generacion=timezone.now()
            )
            counter += 1
        except Exception as e:
            print(f"Error en fila {counter}: {e}")