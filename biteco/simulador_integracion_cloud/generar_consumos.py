import calendar
import json
import random
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import psycopg2
import requests
from psycopg2.extras import execute_values

DB_CONFIG = {
    "dbname": "biteco",
    "user": "admin_biteco",
    "password": "123",
    "host": "172.31.20.130",
    "port": 5432,
}

AGREGADOR_URL = "http://3.80.83.238:8080/api/agregacion/registrar/"

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

REGISTROS_MINIMOS_POR_PROYECTO_MES = 20
SERVICIOS_MINIMOS_POR_PROYECTO_MES = 7
TIMEOUT_REQUEST = 5
MAX_WORKERS_HTTP = 32
TAMANIO_BATCH_HTTP = 500


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
        ORDER BY cc.proveedor, sc.id_servicio_cloud
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


def normalizar_nombre(texto):
    return (
        texto.strip()
        .lower()
        .replace(" ", "-")
        .replace("_", "-")
        .replace("/", "-")
    )


def ultimo_dia_permitido(anio, mes):
    if anio == 2026 and mes == 4:
        return 9
    return calendar.monthrange(anio, mes)[1]


def generar_dias_distribuidos(anio, mes, cantidad):
    """
    Devuelve exactamente 'cantidad' días dentro del mes.
    Puede repetir días cuando cantidad > número de días disponibles.
    Abril 2026 queda limitado al día 9.
    """
    ultimo_dia = ultimo_dia_permitido(anio, mes)
    dias_disponibles = list(range(1, ultimo_dia + 1))

    if cantidad <= ultimo_dia:
        return sorted(random.sample(dias_disponibles, cantidad))

    resultado = dias_disponibles.copy()
    faltantes = cantidad - len(resultado)
    resultado.extend(random.choices(dias_disponibles, k=faltantes))
    return sorted(resultado)


def agrupar_servicios_por_proveedor(servicios):
    servicios_por_proveedor = {
        "AWS": [],
        "AZURE": [],
        "GCP": [],
    }
    for servicio in servicios:
        proveedor = servicio[2]
        servicios_por_proveedor[proveedor].append(servicio)
    return servicios_por_proveedor


def obtener_servicios_distintos_para_proyecto_mes(servicios, cantidad_minima):
    """
    Selecciona al menos N servicios distintos globales.
    Si no existen suficientes, falla explícitamente.
    """
    servicios_unicos = {}
    for s in servicios:
        servicios_unicos[s[0]] = s

    servicios_lista = list(servicios_unicos.values())

    if len(servicios_lista) < cantidad_minima:
        raise RuntimeError(
            f"Se requieren al menos {cantidad_minima} servicios cloud distintos "
            f"y solo hay {len(servicios_lista)} cargados."
        )

    return random.sample(servicios_lista, cantidad_minima)


def construir_payload(proyecto, servicio, id_region, anio, mes, dia, consecutivo):
    id_proyecto, id_area, id_empresa, nombre_proyecto = proyecto
    id_servicio_cloud, nombre_servicio, proveedor, identificador_cuenta = servicio

    resource_prefix = RESOURCE_PREFIX_POR_PROVEEDOR[proveedor]
    nombre_proyecto_norm = normalizar_nombre(nombre_proyecto)
    grupo_recurso = f"rg-{nombre_proyecto_norm}-{anio}{mes:02d}-{dia:02d}"

    costo_base = random.uniform(8.0, 120.0)
    ajuste_mes = mes * 0.8
    ajuste_dia = dia * 0.15
    costo = round(costo_base + ajuste_mes + ajuste_dia, 4)

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


def generar_lote_completo(proyectos, servicios, regiones_por_nombre):
    if not proyectos:
        raise RuntimeError("No hay proyectos disponibles en nucleo.proyectos")

    if not servicios:
        raise RuntimeError("No hay servicios cloud disponibles")

    servicios_por_proveedor = agrupar_servicios_por_proveedor(servicios)

    for proveedor, regiones in REGIONES_POR_PROVEEDOR.items():
        if not servicios_por_proveedor[proveedor]:
            raise RuntimeError(f"No hay servicios cargados para proveedor {proveedor}")
        for region in regiones:
            if region not in regiones_por_nombre:
                raise RuntimeError(f"No existe la región '{region}' en nube.regiones")

    lote = []
    consecutivo = 1

    for proyecto_idx, proyecto in enumerate(proyectos):
        for periodo_idx, (anio, mes) in enumerate(PERIODOS):
            servicios_base = obtener_servicios_distintos_para_proyecto_mes(
                servicios,
                SERVICIOS_MINIMOS_POR_PROYECTO_MES,
            )

            dias = generar_dias_distribuidos(
                anio,
                mes,
                REGISTROS_MINIMOS_POR_PROYECTO_MES,
            )

            for i in range(REGISTROS_MINIMOS_POR_PROYECTO_MES):
                servicio = servicios_base[i % len(servicios_base)]
                proveedor = servicio[2]

                regiones_validas = REGIONES_POR_PROVEEDOR[proveedor]
                region_nombre = regiones_validas[
                    (proyecto_idx + periodo_idx + i) % len(regiones_validas)
                ]
                id_region = regiones_por_nombre[region_nombre]
                dia = dias[i]

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


def insertar_crudo_masivo(cur, lote):
    valores = [
        (
            p["id_proyecto"],
            p["id_servicio_cloud"],
            p["id_region"],
            p["fecha_consumo"],
            p["grupo_recurso"],
            p["costo"],
            p["moneda"],
            p["id_recurso_crudo"],
        )
        for p in lote
    ]

    execute_values(
        cur,
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
        VALUES %s
        """,
        valores,
        page_size=2000,
    )


def post_agregador(payload, session):
    response = session.post(
        AGREGADOR_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=TIMEOUT_REQUEST,
    )
    response.raise_for_status()


def enviar_lote_agregador(lote):
    enviados = 0
    fallidos = 0

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_HTTP) as executor:
            futures = [
                executor.submit(post_agregador, payload, session)
                for payload in lote
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                    enviados += 1
                except Exception:
                    fallidos += 1

    return enviados, fallidos


def chunks(lista, tam):
    for i in range(0, len(lista), tam):
        yield lista[i:i + tam]


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

        lote = generar_lote_completo(
            proyectos=proyectos,
            servicios=servicios,
            regiones_por_nombre=regiones_por_nombre,
        )

        print(f"Total de registros a insertar: {len(lote)}")
        print(
            f"Configuración: {REGISTROS_MINIMOS_POR_PROYECTO_MES} registros por proyecto/mes, "
            f"{SERVICIOS_MINIMOS_POR_PROYECTO_MES} servicios mínimos por proyecto/mes"
        )

        insertar_crudo_masivo(cur, lote)
        conn.commit()
        print("Inserción en BD completada.")

        enviados_total = 0
        fallidos_total = 0

        for idx, batch in enumerate(chunks(lote, TAMANIO_BATCH_HTTP), start=1):
            enviados, fallidos = enviar_lote_agregador(batch)
            enviados_total += enviados
            fallidos_total += fallidos
            print(
                f"Batch HTTP {idx}: enviados={enviados}, fallidos={fallidos}, tamaño={len(batch)}"
            )

        print(
            f"Proceso completado. BD insertados={len(lote)}, "
            f"agregador enviados={enviados_total}, fallidos={fallidos_total}"
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()