import psycopg2
import requests
import random
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from config import AGREGADOR_URL, MONTO_MIN, MONTO_MAX, DELAY, SERVICIOS

load_dotenv()

def obtener_proyectos():
    """Consulta la DB para obtener la lista de proyectos reales."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cur = conn.cursor()
        cur.execute("SELECT empresa_id, id_proyecto FROM core.proyectos;")
        proyectos = cur.fetchall()
        cur.close()
        conn.close()
        return proyectos
    except Exception as e:
        print(f"Error conectando a la DB para leer proyectos: {e}")
        return []

def simular_trafico():
    print("Iniciando Simulador de Tráfico...")
    proyectos_reales = obtener_proyectos()
    
    if not proyectos_reales:
        print("No se encontraron proyectos en la base de datos. Abortando.")
        return

    print(f"Se cargaron {len(proyectos_reales)} combinaciones empresa/proyecto.")

    while True:
        # 1. Elegir un proyecto al azar de la base de datos
        empresa_id, proyecto_id = random.choice(proyectos_reales)

        # 2. Generar datos del gasto
        payload = {
            "empresa_id": empresa_id,
            "proyecto_id": proyecto_id,
            "servicio": random.choice(SERVICIOS),
            "costo": round(random.uniform(MONTO_MIN, MONTO_MAX), 2),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 3. Enviar al Agregador vía POST
        try:
            response = requests.post(AGREGADOR_URL, json=payload, timeout=5)
            if response.status_code == 201:
                print(f"⬆Gasto enviado: Proyecto {proyecto_id} | Monto: ${payload['costo']}")
            else:
                print(f"Error en el Agregador: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"El Agregador no responde: {e}")

        # 4. Esperar según la configuración
        time.sleep(DELAY)

if __name__ == "__main__":
    simular_trafico()