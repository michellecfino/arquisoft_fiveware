import psycopg2
from psycopg2.extras import execute_batch
import os
from dotenv import load_dotenv

load_dotenv()

def seed_database():
    print("Iniciando el proceso de Seeding en AWS RDS...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cur = conn.cursor()

        # 1. Insertar 1,000 Empresas
        print("Insertando 1,000 empresas...")
        empresas = [(f"Empresa Corporativa {i}", f"NIT-{1000+i}", "Tecnología") for i in range(1, 1001)]
        execute_batch(cur, """
            INSERT INTO core.empresas (nombre, nit, sector) 
            VALUES (%s, %s, %s)
        """, empresas)

        # Obtenemos los IDs generados para las empresas
        cur.execute("SELECT id_empresa FROM core.empresas;")
        empresa_ids = [row[0] for row in cur.fetchall()]

        # 2. Insertar 5,000 Proyectos (5 por cada empresa)
        print("Insertando 5,000 proyectos...")
        proyectos = []
        for e_id in empresa_ids:
            for p_idx in range(1, 6):
                proyectos.append((e_id, f"Proyecto Desarrollo {p_idx} - Empresa {e_id}", 100000.00))
        
        execute_batch(cur, """
            INSERT INTO core.proyectos (empresa_id, nombre, presupuesto_asignado) 
            VALUES (%s, %s, %s)
        """, proyectos)

        # 3. Inicializar la Tabla Agregada con costo 0 (Para el UPSERT del Agregador)
        # Esto es para que el reporte ya exista para el mes actual (Marzo 2026)
        print("Inicializando 5,000 registros de resumen mensual (costo 0)...")
        cur.execute("SELECT empresa_id, id_proyecto FROM core.proyectos;")
        proyectos_reales = cur.fetchall()
        
        resumenes = [(p[0], p[1], 2026, 3, 0) for p in proyectos_reales]
        execute_batch(cur, """
            INSERT INTO analytics.resumen_mensual_costos (empresa_id, proyecto_id, anio, mes, costo_total)
            VALUES (%s, %s, %s, %s, %s)
        """, resumenes)

        conn.commit()
        print("Seeding completado exitosamente.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error durante el Seeding: {e}")

if __name__ == "__main__":
    seed_database()