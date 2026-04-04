from django.db import connection, transaction


def agregar_consumo(payload: dict) -> dict:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO reportes.resumen_mensual_costos
                (id_empresa, id_area, id_proyecto, anio, mes, moneda, costo_total, cantidad_registros, ultima_actualizacion)
                VALUES (%s,%s,%s,%s,%s,%s,%s,1,NOW())
                ON CONFLICT (id_empresa, id_area, id_proyecto, anio, mes)
                DO UPDATE SET
                    costo_total = reportes.resumen_mensual_costos.costo_total + EXCLUDED.costo_total,
                    cantidad_registros = reportes.resumen_mensual_costos.cantidad_registros + 1,
                    ultima_actualizacion = NOW()
                RETURNING id_resumen
                """,
                [
                    payload["id_empresa"],
                    payload["id_area"],
                    payload["id_proyecto"],
                    payload["anio"],
                    payload["mes"],
                    payload["moneda"],
                    payload["costo"],
                ],
            )
            id_resumen = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO reportes.detalle_servicio
                (id_resumen, nombre_servicio, cantidad_registros, costo_total, moneda, ultima_actualizacion)
                VALUES (%s,%s,1,%s,%s,NOW())
                ON CONFLICT (id_resumen, nombre_servicio)
                DO UPDATE SET
                    cantidad_registros = reportes.detalle_servicio.cantidad_registros + 1,
                    costo_total = reportes.detalle_servicio.costo_total + EXCLUDED.costo_total,
                    ultima_actualizacion = NOW()
                """,
                [
                    id_resumen,
                    payload["nombre_servicio"],
                    payload["costo"],
                    payload["moneda"],
                ],
            )

    return {"ok": True, "id_resumen": id_resumen}