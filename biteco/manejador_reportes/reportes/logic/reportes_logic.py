import requests
from ..models import ResumenMensualCosto, DetalleServicio

def obtener_reporte(id_proyecto: int, anio: int, mes: int) -> dict:
    # 1. Obtener el resumen principal de la base de datos RDS
    resumen = ResumenMensualCosto.objects.values(
        "id_resumen",
        "id_proyecto",
        "anio",
        "mes",
        "moneda",
        "costo_total",
        "cantidad_registros",
        "ultima_actualizacion",
    ).get(
        id_proyecto=id_proyecto,
        anio=anio,
        mes=mes,
    )

    # 2. Obtener los detalles asociados
    detalles = list(
        DetalleServicio.objects.filter(
            id_resumen=resumen["id_resumen"]
        ).values(
            "nombre_servicio",
            "cantidad_registros",
            "costo_total",
        )
    )

    # 3. Armar el diccionario de respuesta
    resultado = {
        "id_proyecto": resumen["id_proyecto"],
        "periodo": {
            "anio": resumen["anio"],
            "mes": resumen["mes"],
        },
        "moneda": resumen["moneda"],
        "costo_total_mes": float(resumen["costo_total"]),
        "cantidad_registros_consolidados": resumen["cantidad_registros"],
        "desglose_por_servicio": [
            {
                "tipo_servicio": d["nombre_servicio"],
                "cantidad_registros": d["cantidad_registros"],
                "costo_total": float(d["costo_total"]),
            }
            for d in detalles
        ],
        "fecha_generacion": resumen["ultima_actualizacion"].isoformat(),
    }

    # 4. Enviar log al Audit-Server (Instancia 215) vía red interna
    try:
        log_data = {
            "usuario": "sistema_reportes",
            "accion": f"Generación reporte Proyecto {id_proyecto}",
            "metadata": f"Periodo {anio}-{mes} - Instancia: Reportes"
        }
        # Se usa un timeout corto (1s) para no afectar la latencia del usuario
        requests.post("http://10.0.2.215:8002/api/logs", json=log_data, timeout=1)
    except Exception:
        # Si el auditor no responde, el reporte se entrega de todos modos
        pass

    return resultado
