from ..models import ResumenMensualCosto, DetalleServicio


def obtener_reporte(id_proyecto: int, anio: int, mes: int) -> dict:
    resumen = ResumenMensualCosto.objects.get(
        id_proyecto=id_proyecto,
        anio=anio,
        mes=mes,
    )

    detalles = DetalleServicio.objects.filter(
        id_resumen=resumen.id_resumen
    ).order_by("nombre_servicio")

    return {
        "id_proyecto": resumen.id_proyecto,
        "periodo": {
            "anio": resumen.anio,
            "mes": resumen.mes,
        },
        "moneda": resumen.moneda,
        "costo_total_mes": float(resumen.costo_total),
        "cantidad_registros_consolidados": resumen.cantidad_registros,
        "desglose_por_servicio": [
            {
                "tipo_servicio": d.nombre_servicio,
                "cantidad_registros": d.cantidad_registros,
                "costo_total": float(d.costo_total),
            }
            for d in detalles
        ],
        "fecha_generacion": resumen.ultima_actualizacion.isoformat(),
    }