import calendar
import json
import random
import time
import uuid
from datetime import date

import psycopg2
import requests

DB_CONFIG = {
    "dbname": "biteco",
    "user": "admin_biteco",
    "password": "123",
    "host": "172.31.20.130",
    "port": 5432,
}

AGREGADOR_URL = "http://3.89.97.136:8080/api/agregacion/registrar/"

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

REGISTROS_POR_PROYECTO_Y_PERIODO = 3
PAUSA_ENTRE_LOTES_SEGUNDOS = 3
TIMEOUT_REQUEST = 5


def obtener_servicios_cloud(cur):
    cur.execute(
        """
        SELECT
            sc.id_servicio_cloud,
            sc.nombre,
            cc.proveedor,
            cc.identificador
        FROM nube.servicios_cloud sc
        JOIN nube.cuentas_cloud cc
            ON cc.identificador = sc.identificador_cuenta_cloud
        ORDER BY sc.id_servicio_cloud
        """
    )
    return cur.fetchall()


def obtener_proyectos(cur):
    cur.execute(
        """
        SELECT
            p.id_proyecto,
            p.id_area,
            p.id_empresa,
            p.nombre
        FROM nucleo.proyectos p
        ORDER BY p.id_proyecto
        """
    )
    return cur.fetchall()


def obtener_regiones(cur):
    cur.execute(
        """
        SELECT id_region, nombre
        FROM nube.regiones
        """
    )
    rows = cur.fetchall()
    return {nombre: id_region for id_region, nombre in rows}


def insertar_crudo(cur, payload):
    cur.execute(
        """
        INSERT INTO nube.registros_consumo
        (
            id_proyecto,
            id_servicio_cloud,
            id_region,
            fecha_consumo,
            grupo_recurso,
            costo,
            moneda,
            id_recurso_crudo
        )
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


def generar_dias_distribuidos(anio, mes, cantidad):
    """
    Genera días distribuidos dentro del mes, evitando que queden todos
    concentrados al inicio o al final.
    """
    ultimo_dia = calendar.monthrange(anio, mes)[1]

    if cantidad <= 1:
        return [min(15, ultimo_dia)]

    paso = ultimo_dia / (cantidad + 1)
    dias = []

    for i in range(1, cantidad + 1):
        base = int(round(i * paso))
        variacion = random.randint(-2, 2)
        dia = max(1, min(ultimo_dia, base + variacion))
        dias.append(dia)

    dias = sorted(set(dias))

    while len(dias) < cantidad:
        candidato = random.randint(1, ultimo_dia)
        if candidato not in dias:
            dias.append(candidato)

    return sorted(dias[:cantidad])


def normalizar_nombre(texto):
    return (
        texto.strip()
        .lower()
        .replace(" ", "-")
        .replace("_", "-")
        .replace("/", "-")
    )


def construir_payload(
    proyecto,
    servicio,
    id_region,
    anio,
    mes,
    dia,
    consecutivo,
):
    id_proyecto, id_area, id_empresa, nombre_proyecto = proyecto
    id_servicio_cloud, nombre_servicio, proveedor, identificador_cuenta = servicio

    resource_prefix = RESOURCE_PREFIX_POR_PROVEEDOR[proveedor]
    nombre_proyecto_norm = normalizar_nombre(nombre_proyecto)
    grupo_recurso = f"rg-{nombre_proyecto_norm}-{anio}{mes:02d}-{dia:02d}"

    # Costo menos caótico, pero con variación suficiente
    costo_base = random.uniform(2.5, 40.0)
    ajuste = (mes * 0.35) + (dia * 0.07)
    costo = round(costo_base + ajuste, 4)

    return {
        "id_empresa": id_empresa,
        "id_area": id_area,
        "id_proyecto": id_proyecto,
        "id_servicio_cloud": id_servicio_cloud,
        "id_region": id_region,
        "fecha_consumo": str(date(anio, mes, dia)),
        "grupo_recurso": grupo_recurso,
        "costo": costo,
        "moneda": "USD",
        "id_recurso_crudo": (
            f"/subscriptions/{identificador_cuenta}"
            f"/resourcegroups/{grupo_recurso}"
            f"/providers/{resource_prefix}/resource-{consecutivo}-{uuid.uuid4()}"
        ),
        "nombre_servicio": nombre_servicio,
        "anio": anio,
        "mes": mes,
    }


def post_agregador(payload):
    response = requests.post(
        AGREGADOR_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=TIMEOUT_REQUEST,
    )
    response.raise_for_status()


def generar_lote_completo(proyectos, servicios, regiones_por_nombre):
    """
    Genera un lote garantizando:
    - todos los proyectos
    - todos los periodos
    - varios días dentro de cada mes
    - servicios y regiones coherentes con el proveedor
    """
    if not proyectos:
        raise RuntimeError("No hay proyectos disponibles en nucleo.proyectos")

    if not servicios:
        raise RuntimeError("No hay servicios cloud disponibles")

    lote = []
    consecutivo = 1

    servicios_por_proveedor = {
        "AWS": [s for s in servicios if s[2] == "AWS"],
        "AZURE": [s for s in servicios if s[2] == "AZURE"],
        "GCP": [s for s in servicios if s[2] == "GCP"],
    }

    for proveedor, regiones in REGIONES_POR_PROVEEDOR.items():
        if not servicios_por_proveedor[proveedor]:
            raise RuntimeError(f"No hay servicios cargados para proveedor {proveedor}")

        for region in regiones:
            if region not in regiones_por_nombre:
                raise RuntimeError(
                    f"No existe la región '{region}' en nube.regiones"
                )

    proveedores = list(REGIONES_POR_PROVEEDOR.keys())

    for proyecto_idx, proyecto in enumerate(proyectos):
        for periodo_idx, (anio, mes) in enumerate(PERIODOS):
            dias = generar_dias_distribuidos(
                anio,
                mes,
                REGISTROS_POR_PROYECTO_Y_PERIODO,
            )

            # Alterna proveedor de forma controlada para no dejar todo al azar
            proveedor_base = proveedores[(proyecto_idx + periodo_idx) % len(proveedores)]

            for i, dia in enumerate(dias):
                proveedor = proveedores[
                    (proveedores.index(proveedor_base) + i) % len(proveedores)
                ]

                servicio = random.choice(servicios_por_proveedor[proveedor])
                region_nombre = REGIONES_POR_PROVEEDOR[proveedor][
                    (proyecto_idx + periodo_idx + i) % len(REGIONES_POR_PROVEEDOR[proveedor])
                ]
                id_region = regiones_por_nombre[region_nombre]

                payload = construir_payload(
                    proyecto=proyecto,
                    servicio=servicio,
                    id_region=id_region,
                    anio=anio,
                    mes=mes,
                    dia=dia,
                    consecutivo=consecutivo,
                )
                lote.append(payload)
                consecutivo += 1

    random.shuffle(lote)
    return lote


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        proyectos = obtener_proyectos(cur)
        servicios = obtener_servicios_cloud(cur)
        regiones_por_nombre = obtener_regiones(cur)

        print(f"Proyectos encontrados: {len(proyectos)}")
        print(f"Servicios encontrados: {len(servicios)}")
        print("Iniciando generación continua de lotes...")

        while True:
            lote = generar_lote_completo(
                proyectos=proyectos,
                servicios=servicios,
                regiones_por_nombre=regiones_por_nombre,
            )

            insertados = 0
            enviados = 0

            try:
                for payload in lote:
                    insertar_crudo(cur, payload)
                    insertados += 1

                    try:
                        post_agregador(payload)
                        enviados += 1
                    except requests.RequestException as e:
                        print(
                            f"[WARN] Falló POST al agregador para proyecto "
                            f"{payload['id_proyecto']} fecha {payload['fecha_consumo']}: {e}"
                        )

                conn.commit()
                print(
                    f"Lote completado. Insertados BD: {insertados}, "
                    f"enviados agregador: {enviados}, total lote: {len(lote)}"
                )

            except Exception:
                conn.rollback()
                raise

            time.sleep(PAUSA_ENTRE_LOTES_SEGUNDOS)

    finally:
        conn.close()


if __name__ == "__main__":
    main()