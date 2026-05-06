import sys
import os
import csv
from django.utils import timezone

# -----------------------------
# Ajuste de PYTHONPATH
# -----------------------------
# Permite que Python encuentre el paquete manejador_reportes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# -----------------------------
# Configuración de Django
# -----------------------------
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manejador_reportes.settings")
django.setup()

# -----------------------------
# Importar modelos
# -----------------------------
from reportes.models import ReporteGenerado
from nucleo.models import Proyecto, Usuario

# -----------------------------
# Configuración del CSV
# -----------------------------
CSV_PATH = os.path.expanduser(
    '~/arquisoft_fiveware/biteco/jmeter/data/solicitudes_20000.csv'
)

# -----------------------------
# Preparar datos
# -----------------------------
# Obtener un usuario de prueba (ajusta si quieres otro)
usuario = Usuario.objects.first()
if not usuario:
    raise Exception("No hay usuarios en la base de datos. Crea al menos uno.")

# Lista para almacenar los objetos a insertar
registros_a_crear = []

# Contador para generar request_id único
counter = 1

# -----------------------------
# Leer CSV y crear objetos
# -----------------------------
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            proyecto = Proyecto.objects.get(pk=int(row['id_proyecto']))
            reporte = ReporteGenerado(
                id_empresa=proyecto.id_empresa,
                id_area=proyecto.id_area,
                id_proyecto=proyecto.id_proyecto,
                id_usuario=usuario.id_usuario,
                anio=int(row['anio']),
                mes=int(row['mes']),
                moneda='COP',  # Ajusta si quieres 'USD' o 'EUR'
                total_costo=0,
                cantidad_registros=0,
                request_id=f'test-{counter}',
                instancia_origen='manejador_reportes',
                fecha_generacion=timezone.now()
            )
            registros_a_crear.append(reporte)
            counter += 1

            # Insertar en bloques de 1000 para no saturar la memoria
            if len(registros_a_crear) >= 1000:
                ReporteGenerado.objects.bulk_create(registros_a_crear)
                registros_a_crear = []

        except Proyecto.DoesNotExist:
            print(f"Proyecto {row['id_proyecto']} no encontrado, fila {counter}")
        except Exception as e:
            print(f"Error en fila {counter}: {e}")

# Insertar los que queden
if registros_a_crear:
    ReporteGenerado.objects.bulk_create(registros_a_crear)

print(f"Importación finalizada. Total de registros creados: {counter - 1}")