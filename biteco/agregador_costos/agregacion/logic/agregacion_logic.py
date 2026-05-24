from django.db import connection, transaction


def agregar_consumo(payload: dict) -> dict:
    print("[AGREGADOR][LOGIC] Iniciando transaccion")

    with transaction.atomic():
        with connection.cursor() as cursor:
            print(
                "[AGREGADOR][LOGIC] UPSERT resumen para "
                f"proyecto={payload['id_proyecto']} periodo={payload['anio']}-{payload['mes']} "
                f"costo={payload['costo']} servicio={payload['nombre_servicio']}"
            )

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
                RETURNING id_resumen, costo_total, cantidad_registros
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
            resumen_row = cursor.fetchone()
            id_resumen = resumen_row[0]

            print(
                "[AGREGADOR][LOGIC] Resumen actualizado -> "
                f"id_resumen={resumen_row[0]}, costo_total={resumen_row[1]}, cantidad_registros={resumen_row[2]}"
            )

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
                RETURNING cantidad_registros, costo_total
                """,
                [
                    id_resumen,
                    payload["nombre_servicio"],
                    payload["costo"],
                    payload["moneda"],
                ],
            )
            detalle_row = cursor.fetchone()

            print(
                "[AGREGADOR][LOGIC] Detalle actualizado -> "
                f"servicio={payload['nombre_servicio']}, cantidad_registros={detalle_row[0]}, costo_total={detalle_row[1]}"
            )

    print("[AGREGADOR][LOGIC] Transaccion completada")

    return {
        "ok": True,
        "id_resumen": id_resumen,
        "nombre_servicio": payload["nombre_servicio"],
    }