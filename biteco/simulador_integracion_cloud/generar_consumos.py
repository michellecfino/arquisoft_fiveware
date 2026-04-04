import json
import random
import time
import uuid
from datetime import date
import requests
import psycopg2

DB_CONFIG = {
    "dbname": "biteco",
    "user": "admin_biteco",
    "password": "123",
    "host": "localhost",
    "port": 5432,
}

AGREGADOR_URL = "http://127.0.0.1:8001/api/agregacion/registrar/"

SERVICIOS_AZURE = [
    "Azure App Service",
    "Azure DNS",
    "Container Registry",
    "Virtual Network",
    "Virtual Machines",
    "Storage",
    "Application Gateway",
    "Azure Bastion",
    "Bandwidth",
    "Log Analytics",
    "Load Balancer",
    "Microsoft Entra Domain Services",
]

PERIODOS = [
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4),
]


def obtener_servicio_cloud(cur):
    cur.execute("""
        SELECT sc.id_servicio_cloud, sc.nombre, cc.proveedor
        FROM nube.servicios_cloud sc
        JOIN nube.cuentas_cloud cc
          ON cc.identificador = sc.identificador_cuenta_cloud
        ORDER BY RANDOM()
        LIMIT 1
    """)
    return cur.fetchone()


def obtener_proyecto(cur):
    cur.execute("""
        SELECT p.id_proyecto, p.id_area, p.id_empresa
        FROM nucleo.proyectos p
        ORDER BY RANDOM()
        LIMIT 1
    """)
    return cur.fetchone()


def obtener_region(cur):
    cur.execute("""
        SELECT id_region, nombre
        FROM nube.regiones
        ORDER BY RANDOM()
        LIMIT 1
    """)
    return cur.fetchone()


def insertar_crudo(cur, payload):
    cur.execute(
        """
        INSERT INTO nube.registros_consumo
        (id_proyecto, id_servicio_cloud, id_region, fecha_consumo, grupo_recurso, costo, moneda, id_recurso_crudo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        [
            payload["id_proyecto"],
            payload["id_servicio_cloud"],
            payload["id_region"],
            payload["fecha_consumo"],
            payload["grupo_recurso"],
            payload["costo"],
            payload["moneda"],
            payload["id_recurso_crudo"],
        ],
    )


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    while True:
        lote = random.randint(20, 40)

        for _ in range(lote):
            proyecto = obtener_proyecto(cur)
            servicio = obtener_servicio_cloud(cur)
            region = obtener_region(cur)
            anio, mes = random.choice(PERIODOS)
            dia = random.randint(1, 28)

            id_proyecto, id_area, id_empresa = proyecto
            id_servicio_cloud, nombre_servicio, proveedor = servicio
            id_region, nombre_region = region

            payload = {
                "id_empresa": id_empresa,
                "id_area": id_area,
                "id_proyecto": id_proyecto,
                "id_servicio_cloud": id_servicio_cloud,
                "id_region": id_region,
                "fecha_consumo": str(date(anio, mes, dia)),
                "grupo_recurso": f"rg-{id_proyecto}-{mes}",
                "costo": round(random.uniform(0.01, 12.0), 4),
                "moneda": "USD",
                "id_recurso_crudo": f"/subscriptions/{uuid.uuid4()}/resourcegroups/rg-{id_proyecto}/providers/{proveedor.lower()}/{uuid.uuid4()}",
                "nombre_servicio": nombre_servicio,
                "anio": anio,
                "mes": mes,
            }

            insertar_crudo(cur, payload)
            requests.post(
                AGREGADOR_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=5,
            )

        conn.commit()
        print(f"Lote insertado y agregado: {lote} registros")
        time.sleep(3)


if __name__ == "__main__":
    main()