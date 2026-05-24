from django.db import connection, transaction
from datetime import datetime

def agregar_consumo(payload: dict) -> dict:
    """
    Agrega un registro de consumo y actualiza los resúmenes
    Payload esperado:
    {
        "id_empresa": int,
        "id_area": int,
        "id_proyecto": int,
        "anio": int,
        "mes": int,
        "moneda": str,
        "costo": decimal,
        "nombre_servicio": str
    }
    """
    print("[AGREGADOR][LOGIC] Iniciando transaccion")
    
    # Validaciones básicas
    required_fields = ['id_empresa', 'id_area', 'id_proyecto', 'anio', 'mes', 'moneda', 'costo', 'nombre_servicio']
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    with transaction.atomic():
        with connection.cursor() as cursor:
            # UPSERT para el resumen mensual
            cursor.execute(
                """
                INSERT INTO reportes.resumen_mensual_costos
                (id_empresa, id_area, id_proyecto, anio, mes, moneda, costo_total, cantidad_registros, ultima_actualizacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
                ON CONFLICT (id_empresa, id_area, id_proyecto, anio, mes)
                DO UPDATE SET
                    costo_total = reportes.resumen_mensual_costos.costo_total + EXCLUDED.costo_total,
                    cantidad_registros = reportes.resumen_mensual_costos.cantidad_registros + 1,
                    ultima_actualizacion = %s
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
                    datetime.now(),
                    datetime.now()
                ],
            )
            resumen_row = cursor.fetchone()
            if not resumen_row:
                raise Exception("Error al insertar/actualizar resumen")
                
            id_resumen = resumen_row[0]
            
            print(f"[AGREGADOR][LOGIC] Resumen actualizado -> id_resumen={id_resumen}, "
                  f"costo_total={resumen_row[1]}, cantidad_registros={resumen_row[2]}")
            
            # UPSERT para el detalle por servicio
            cursor.execute(
                """
                INSERT INTO reportes.detalle_servicio
                (id_resumen, nombre_servicio, cantidad_registros, costo_total, moneda, ultima_actualizacion)
                VALUES (%s, %s, 1, %s, %s, %s)
                ON CONFLICT (id_resumen, nombre_servicio)
                DO UPDATE SET
                    cantidad_registros = reportes.detalle_servicio.cantidad_registros + 1,
                    costo_total = reportes.detalle_servicio.costo_total + EXCLUDED.costo_total,
                    ultima_actualizacion = %s
                RETURNING cantidad_registros, costo_total
                """,
                [
                    id_resumen,
                    payload["nombre_servicio"],
                    payload["costo"],
                    payload["moneda"],
                    datetime.now(),
                    datetime.now()
                ],
            )
            detalle_row = cursor.fetchone()
            
            print(f"[AGREGADOR][LOGIC] Detalle actualizado -> servicio={payload['nombre_servicio']}, "
                  f"cantidad_registros={detalle_row[0]}, costo_total={detalle_row[1]}")
    
    print("[AGREGADOR][LOGIC] Transaccion completada")
    
    return {
        "ok": True,
        "id_resumen": id_resumen,
        "nombre_servicio": payload["nombre_servicio"],
        "costo_acumulado": float(resumen_row[1]),
        "total_registros": resumen_row[2],
        "mensaje": "Consumo registrado exitosamente"
    }

def consultar_resumen_por_id(id_resumen: int) -> dict:
    """Consultar resumen por ID"""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_resumen, id_empresa, id_area, id_proyecto, anio, mes, 
                   moneda, costo_total, cantidad_registros, ultima_actualizacion
            FROM reportes.resumen_mensual_costos
            WHERE id_resumen = %s
            """,
            [id_resumen]
        )
        row = cursor.fetchone()
    
    if not row:
        return None
    
    return {
        "id_resumen": row[0],
        "id_empresa": row[1],
        "id_area": row[2],
        "id_proyecto": row[3],
        "anio": row[4],
        "mes": row[5],
        "moneda": row[6],
        "costo_total": float(row[7]),
        "cantidad_registros": row[8],
        "ultima_actualizacion": row[9].isoformat() if row[9] else None
    }

def listar_resumenes(filtros: dict = None) -> list:
    """Listar resúmenes con filtros opcionales"""
    query = """
        SELECT id_resumen, id_empresa, id_area, id_proyecto, anio, mes, 
               moneda, costo_total, cantidad_registros
        FROM reportes.resumen_mensual_costos
        WHERE 1=1
    """
    params = []
    
    if filtros:
        if filtros.get('id_empresa'):
            query += " AND id_empresa = %s"
            params.append(filtros['id_empresa'])
        if filtros.get('id_proyecto'):
            query += " AND id_proyecto = %s"
            params.append(filtros['id_proyecto'])
        if filtros.get('anio'):
            query += " AND anio = %s"
            params.append(filtros['anio'])
        if filtros.get('mes'):
            query += " AND mes = %s"
            params.append(filtros['mes'])
    
    query += " ORDER BY anio DESC, mes DESC, id_empresa, id_proyecto"
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    return [
        {
            "id_resumen": row[0],
            "id_empresa": row[1],
            "id_area": row[2],
            "id_proyecto": row[3],
            "anio": row[4],
            "mes": row[5],
            "moneda": row[6],
            "costo_total": float(row[7]),
            "cantidad_registros": row[8]
        }
        for row in rows
    ]