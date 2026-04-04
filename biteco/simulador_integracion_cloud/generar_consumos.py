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

PERIODOS = [
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4),
]

REGIONES_POR_PROVEEDOR = {
    "AWS": ["us-east-2", "us-east-1", "us-west-2"],
    "AZURE": ["us east 2", "us east", "global"],
    "GCP": ["us-central1", "us-east1", "global"],
}

RESOURCE_PREFIX_POR_PROVEEDOR = {
    "AWS": "aws",
    "AZURE": "microsoft",
    "GCP": "google",
}


def obtener_servicio_cloud(cur):
    cur.execute(
        """
        SELECT sc.id_servicio_cloud, sc.nombre, cc.proveedor, cc.identificador
        FROM nube.servicios_cloud sc
        JOIN nube.cuentas_cloud cc
          ON cc.identificador = sc.identificador_cuenta_cloud
        ORDER BY RANDOM()
        LIMIT 1
        """
    )
    return cur.fetchone()


def obtener_proyecto(cur):
    cur.execute(
        """
        SELECT p.id_proyecto, p.id_area, p.id_empresa, p.nombre
        FROM nucleo.proyectos p
        ORDER BY RANDOM()
        LIMIT 1
        """
    )
    return cur.fetchone()


def obtener_id_region(cur, nombre_region):
    cur.execute(
        """
        SELECT id_region
        FROM nube.regiones
        WHERE nombre = %s
        LIMIT 1
        """,
        [nombre_region],
    )
    row = cur.fetchone()
    return row[0] if row else None


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


def construir_payload(cur):
    proyecto = obtener_proyecto(cur)
    servicio = obtener_servicio_cloud(cur)

    id_proyecto, id_area, id_empresa, nombre_proyecto = proyecto
    id_servicio_cloud, nombre_servicio, proveedor, identificador_cuenta = servicio

    anio, mes = random.choice(PERIODOS)
    dia = random.randint(1, 28)
    region = random.choice(REGIONES_POR_PROVEEDOR[proveedor])
    id_region = obtener_id_region(cur, region)

    costo = round(random.uniform(0.01, 12.0), 4)
    grupo_recurso = f"rg-{nombre_proyecto}-{mes}".lower().replace(" ", "-")
    resource_prefix = RESOURCE_PREFIX_POR_PROVEEDOR[proveedor]

    payload = {
        "id_empresa": id_empresa,
        "id_area": id_area,
        "id_proyecto": id_proyecto,
        "id_servicio_cloud": id_servicio_cloud,
        "id_region": id_region,
        "fecha_consumo": str(date(anio, mes, dia)),
        "grupo_recurso": grupo_recurso,
        "costo": costo,
        "moneda": "USD",
        "id_recurso_crudo": f"/subscriptions/{identificador_cuenta}/resourcegroups/{grupo_recurso}/providers/{resource_prefix}/{uuid.uuid4()}",
        "nombre_servicio": nombre_servicio,
        "anio": anio,
        "mes": mes,
    }
    return payload


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    while True:
        lote = random.randint(20, 40)

        for _ in range(lote):
            payload = construir_payload(cur)
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