import json
import os
import uuid
import requests
from django.db import connection


CORREO_DESTINO_FIJO = "usuario_test@biteco.com"


def publicar_en_broker(payload):
    url = (
        f"http://{os.getenv('RABBITMQ_HOST')}:{os.getenv('RABBITMQ_API_PORT')}"
        f"/api/exchanges/%2F/{os.getenv('RABBITMQ_EXCHANGE')}/publish"
    )

    body = {
        "properties": {},
        "routing_key": os.getenv("RABBITMQ_ROUTING_KEY"),
        "payload": json.dumps(payload),
        "payload_encoding": "string",
    }

    response = requests.post(
        url,
        auth=(os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASSWORD")),
        json=body,
        timeout=10,
    )
    response.raise_for_status()


def obtener_contexto_solicitud(id_proyecto):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                p.id_empresa,
                p.id_area,
                (
                    SELECT u.id_usuario
                    FROM nucleo.usuarios u
                    WHERE u.id_empresa = p.id_empresa
                      AND u.activo = TRUE
                    ORDER BY u.id_usuario
                    LIMIT 1
                ) AS id_usuario
            FROM nucleo.proyectos p
            WHERE p.id_proyecto = %s
            """,
            [id_proyecto],
        )
        row = cursor.fetchone()

    if not row:
        raise ValueError("No se pudo resolver empresa, area o usuario para la solicitud")

    if row[2] is None:
        raise ValueError("No existe un usuario activo asociado a la empresa del proyecto")

    return {
        "id_empresa": row[0],
        "id_area": row[1],
        "id_usuario": row[2],
        "correo_destino": CORREO_DESTINO_FIJO,
    }


def obtener_reporte(id_proyecto, anio, mes):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                rc.id_proyecto,
                EXTRACT(YEAR FROM rc.fecha_consumo)::int AS anio,
                EXTRACT(MONTH FROM rc.fecha_consumo)::int AS mes,
                MIN(rc.moneda::text) AS moneda,
                COALESCE(SUM(rc.costo), 0) AS costo_total,
                COUNT(*) AS cantidad_registros
            FROM nube.registros_consumo rc
            WHERE rc.id_proyecto = %s
              AND EXTRACT(YEAR FROM rc.fecha_consumo) = %s
              AND EXTRACT(MONTH FROM rc.fecha_consumo) = %s
            GROUP BY rc.id_proyecto, EXTRACT(YEAR FROM rc.fecha_consumo), EXTRACT(MONTH FROM rc.fecha_consumo)
            """,
            [id_proyecto, anio, mes],
        )
        resumen = cursor.fetchone()

        if not resumen:
            raise ValueError("No hay datos para ese proyecto y periodo")

        cursor.execute(
            """
            SELECT
                sc.nombre,
                COUNT(*) AS cantidad_registros,
                COALESCE(SUM(rc.costo), 0) AS costo_total
            FROM nube.registros_consumo rc
            JOIN nube.servicios_cloud sc
              ON sc.id_servicio_cloud = rc.id_servicio_cloud
            WHERE rc.id_proyecto = %s
              AND EXTRACT(YEAR FROM rc.fecha_consumo) = %s
              AND EXTRACT(MONTH FROM rc.fecha_consumo) = %s
            GROUP BY sc.nombre
            ORDER BY costo_total DESC
            """,
            [id_proyecto, anio, mes],
        )
        detalles = cursor.fetchall()

    return {
        "id_proyecto": resumen[0],
        "periodo": {"anio": resumen[1], "mes": resumen[2]},
        "moneda": resumen[3],
        "costo_total_mes": float(resumen[4]),
        "cantidad_registros_consolidados": resumen[5],
        "desglose_por_servicio": [
            {
                "tipo_servicio": row[0],
                "cantidad_registros": row[1],
                "costo_total": float(row[2]),
            }
            for row in detalles
        ],
    }


def registrar_reporte_y_notificacion(id_proyecto, anio, mes, reporte):
    contexto = obtener_contexto_solicitud(id_proyecto)
    id_empresa = contexto["id_empresa"]
    id_area = contexto["id_area"]
    id_usuario = contexto["id_usuario"]
    correo_destino = contexto["correo_destino"]

    request_id = str(uuid.uuid4())
    instancia_origen = os.getenv("REPORTES_INSTANCE_NAME", "reportes-instance")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO reportes.reportes_generados
            (
                id_empresa, id_area, id_proyecto, id_usuario, anio, mes,
                moneda, total_costo, cantidad_registros, request_id,
                instancia_origen, fecha_generacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id_reporte
            """,
            [
                id_empresa,
                id_area,
                id_proyecto,
                id_usuario,
                anio,
                mes,
                reporte["moneda"],
                reporte["costo_total_mes"],
                reporte["cantidad_registros_consolidados"],
                request_id,
                instancia_origen,
            ],
        )
        id_reporte = cursor.fetchone()[0]

        mensaje = f"El reporte mensual del proyecto {id_proyecto} para {anio}-{mes:02d} fue generado."
        url_acceso = f"/reportes/{id_proyecto}/{anio}/{mes}/"

        cursor.execute(
            """
            INSERT INTO nucleo.notificaciones
            (
                id_usuario, id_reporte, correo_destino, fecha_creacion,
                estado, broker_message_id, smtp_message_id, intentos,
                mensaje, url_acceso, error_detalle
            )
            VALUES (%s, %s, %s, NOW(), 'Encolada', %s, NULL, 0, %s, %s, NULL)
            RETURNING id_notificacion
            """,
            [id_usuario, id_reporte, correo_destino, request_id, mensaje, url_acceso],
        )
        id_notificacion = cursor.fetchone()[0]

    payload = {
        "id_notificacion": id_notificacion,
        "id_reporte": id_reporte,
        "id_usuario": id_usuario,
        "correo_destino": correo_destino,
        "mensaje": mensaje,
        "url_acceso": url_acceso,
        "request_id": request_id,
    }

    publicar_en_broker(payload)

    return {
        "id_reporte": id_reporte,
        "id_notificacion": id_notificacion,
        "request_id": request_id,
        "estado_notificacion": "Encolada",
    }


def obtener_reporte_y_notificar(id_proyecto, anio, mes):
    reporte = obtener_reporte(id_proyecto, anio, mes)
    meta = registrar_reporte_y_notificacion(
        id_proyecto=id_proyecto,
        anio=anio,
        mes=mes,
        reporte=reporte,
    )

    return {
        "id_reporte": meta["id_reporte"],
        "id_notificacion": meta["id_notificacion"],
        "request_id": meta["request_id"],
        "estado_notificacion": meta["estado_notificacion"],
        "reporte": reporte,
    }