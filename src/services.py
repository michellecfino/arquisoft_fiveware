"""
services.py — Capa de Servicio: consulta de reportes de proyectos.

===========================================================================
TÁCTICA 2: TIMEOUT (capa de servicio)
===========================================================================
La función get_project_report ejecuta una consulta SQL que simula carga de
datos reales de reportes. El timeout de 200ms se aplica a nivel de sesión
de PostgreSQL (configurado en settings.py > DATABASES > OPTIONS), por lo
que cualquier consulta que supere este umbral será cancelada por el motor
de base de datos con:

    django.db.utils.OperationalError:
        canceling statement due to statement timeout

Este error es capturado en views.py para retornar la respuesta degradada.

Flujo normal (happy path, < 100ms):
    [Request] → get_project_report(project_id) → [SQL] → [datos] → [JSON]

Flujo de fallo de timeout (> 200ms):
    [Request] → get_project_report(project_id) → [SQL] → OperationalError
                                                               ↓
                                                     views.py → graceful_failure

Nota sobre el ASR:
    El escenario define:
      - 100ms: tiempo normal de procesamiento
      - 300ms adicionales como presupuesto máximo para manejo de falla
      - 400ms: tiempo de respuesta total máximo
    El timeout de 200ms garantiza que la query nunca consuma más del presupuesto
    normal, dejando margen para detección + respuesta degradada dentro de 400ms.
===========================================================================
"""

import logging
import time

from django.db import connection, OperationalError, DatabaseError

logger = logging.getLogger("disponibilidad.services")

# ---------------------------------------------------------------------------
# Tipos de datos de resultado
# ---------------------------------------------------------------------------

# Representación de un reporte de proyecto
ProjectReport = dict


class ServiceUnavailableError(Exception):
    """Excepción semántica levantada cuando la DB no responde a tiempo."""
    pass


# ---------------------------------------------------------------------------
# Función principal del servicio
# ---------------------------------------------------------------------------

def get_project_report(project_id: int) -> ProjectReport:
    """
    Obtiene los datos de reporte de un proyecto desde la base de datos.

    Esta función encapsula la consulta SQL y está diseñada para ser consumida
    por la vista. Si la DB falla (timeout, conexión caída), propaga la excepción
    para que la capa de vista aplique la táctica de Degradation.

    Args:
        project_id: Identificador único del proyecto a consultar.

    Returns:
        Dict con los datos del reporte del proyecto.

    Raises:
        ServiceUnavailableError: Si la consulta excede el timeout o la DB no
                                 está disponible. La vista la captura para
                                 retornar la respuesta degradada.
    """
    start_time = time.monotonic()
    logger.info("Iniciando consulta de reporte para project_id=%d", project_id)

    try:
        with connection.cursor() as cursor:
            # ------------------------------------------------------------------
            # Consulta SQL que simula carga real de datos de reportes.
            #
            # En un sistema real, esta query haría JOINs con tablas de métricas,
            # KPIs y actividades del proyecto. Para el experimento, usamos
            # pg_sleep para simular latencia variable:
            #
            #   - Caso normal (< 100ms): pg_sleep(0) — respuesta inmediata
            #   - Caso de stress: pg_sleep(0.25) — excede el timeout de 200ms
            #     y dispara el OperationalError que activa la Degradación.
            #
            # En producción, reemplazar pg_sleep con la query real.
            # ------------------------------------------------------------------
            cursor.execute(
                """
                SELECT
                    p.id                          AS project_id,
                    p.name                        AS project_name,
                    p.status                      AS project_status,
                    COUNT(t.id)                   AS total_tasks,
                    SUM(CASE WHEN t.completed THEN 1 ELSE 0 END) AS completed_tasks,
                    ROUND(
                        100.0 * SUM(CASE WHEN t.completed THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(t.id), 0),
                        2
                    )                             AS completion_percentage,
                    MAX(t.updated_at)             AS last_activity,
                    -- Simular latencia de procesamiento (ajustar en pruebas)
                    pg_sleep(0)                   AS _latency_probe
                FROM projects p
                LEFT JOIN tasks t ON t.project_id = p.id
                WHERE p.id = %s
                GROUP BY p.id, p.name, p.status
                """,
                [project_id],
            )
            row = cursor.fetchone()

        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info("Consulta completada en %.2fms para project_id=%d", elapsed_ms, project_id)

        if row is None:
            logger.warning("No se encontró reporte para project_id=%d", project_id)
            return {
                "project_id": project_id,
                "found": False,
                "data": None,
            }

        # Mapear row a dict con nombres descriptivos
        project_id_col, name, status, total, completed, pct, last_activity, _ = row
        return {
            "project_id": project_id_col,
            "found": True,
            "data": {
                "project_name": name,
                "project_status": status,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_percentage": float(pct) if pct is not None else 0.0,
                "last_activity": last_activity.isoformat() if last_activity else None,
            },
            "query_time_ms": round(elapsed_ms, 2),
        }

    except OperationalError as db_err:
        # ------------------------------------------------------------------
        # TÁCTICA 2: TIMEOUT — captura del error de PostgreSQL
        # ------------------------------------------------------------------
        # PostgreSQL lanza OperationalError con "canceling statement due to
        # statement timeout" cuando se exceden los 200ms configurados.
        # Lo reenvolvemos en ServiceUnavailableError para que views.py
        # pueda distinguirlo semánticamente y retornar la respuesta degradada.
        # ------------------------------------------------------------------
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.error(
            "Timeout o error operacional en consulta DB (%.2fms): %s",
            elapsed_ms,
            db_err,
        )
        raise ServiceUnavailableError(
            f"La consulta a la base de datos excedió el límite de tiempo ({elapsed_ms:.0f}ms)"
        ) from db_err

    except DatabaseError as db_err:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.error(
            "Error de base de datos inesperado (%.2fms): %s",
            elapsed_ms,
            db_err,
        )
        raise ServiceUnavailableError(
            "Error inesperado al consultar la base de datos"
        ) from db_err
