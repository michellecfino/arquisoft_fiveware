import psycopg2
from psycopg2.extras import execute_batch
import os
from dotenv import load_dotenv

load_dotenv()

def seed_database():
    print("Iniciando Seeding")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cur = conn.cursor()

        print("Insertando 1,000 empresas...")
        empresas = [(f"Empresa Corp {i}",) for i in range(1, 1001)]
        execute_batch(cur, "INSERT INTO nucleo.empresas (nombre) VALUES (%s) RETURNING id_empresa;", empresas)
        
        cur.execute("SELECT id_empresa FROM nucleo.empresas;")
        empresa_ids = [row[0] for row in cur.fetchall()]

        print("Insertando áreas por empresa")
        areas = [(e_id, "TI Principal") for e_id in empresa_ids]
        execute_batch(cur, "INSERT INTO nucleo.areas (id_empresa, nombre) VALUES (%s, %s);", areas)

        cur.execute("SELECT id_area, id_empresa FROM nucleo.areas;")
        areas_reales = {row[1]: row[0] for row in cur.fetchall()}

        print("🏗️ Insertando 5,000 proyectos...")
        proyectos = []
        for e_id in empresa_ids:
            a_id = areas_reales[e_id]
            for p_idx in range(1, 6):
                proyectos.append((e_id, a_id, f"Proyecto Cloud {p_idx} - E{e_id}"))
        
        execute_batch(cur, """
            INSERT INTO nucleo.proyectos (id_empresa, id_area, nombre) 
            VALUES (%s, %s, %s)
        """, proyectos)

        print("Creando usuarios para enviar correos")
        usuarios = [(f"Usuario {e_id}", f"user{e_id}@test.com", e_id) for e_id in empresa_ids]
        execute_batch(cur, """
            INSERT INTO nucleo.usuarios (nombre, correo, id_empresa) 
            VALUES (%s, %s, %s)
        """, usuarios)

        print("Inicializando 5,000 resúmenes")
        cur.execute("SELECT id_empresa, id_area, id_proyecto FROM nucleo.proyectos;")
        proyectos_reales = cur.fetchall()
        
        resumenes = [(p[0], p[1], p[2], 2026, 3, "USD", 0) for p in proyectos_reales]
        execute_batch(cur, """
            INSERT INTO reportes.resumen_mensual_costos 
            (id_empresa, id_area, id_proyecto, anio, mes, moneda, costo_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, resumenes)

        conn.commit()
        print("Seeding listo")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error durante el Seeding: {e}")
        if conn: conn.rollback()

if __name__ == "__main__":
    seed_database()