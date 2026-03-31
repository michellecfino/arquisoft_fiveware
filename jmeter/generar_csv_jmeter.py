import psycopg2
import csv
import os
from dotenv import load_dotenv

load_dotenv()

def exportar_datos_jmeter():
    print("Conectando a RDS para extraer combinaciones de prueba...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cur = conn.cursor()
        
        # Obtenemos las 5,000 combinaciones que creaste en el Seeding
        query = "SELECT empresa_id, id_proyecto FROM core.proyectos LIMIT 5000;"
        cur.execute(query)
        rows = cur.fetchall()

        # Guardamos en un archivo CSV compatible con JMeter
        archivo_nombre = 'datos_prueba.csv'
        with open(archivo_nombre, 'w', newline='') as f:
            writer = csv.writer(f)
            # No ponemos encabezados para que JMeter lea directo los datos
            writer.writerows(rows)
        
        print(f"¡Éxito! Se generó '{archivo_nombre}' con {len(rows)} filas.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error al exportar: {e}")

if __name__ == "__main__":
    exportar_datos_jmeter()