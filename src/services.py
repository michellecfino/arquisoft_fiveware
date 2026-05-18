"""
services.py — Capa de Servicio: consulta y almacenamiento de reportes.

===========================================================================
TÁCTICA 2: TIMEOUT (capa de servicio)
===========================================================================
La función get_project_report ejecuta una consulta SQL con datos reales
del modelo Django. El timeout de 1000ms (200ms en consultas críticas) se aplica
a nivel de sesión de PostgreSQL (configurado en settings.py > DATABASES > OPTIONS),
por lo que cualquier consulta que supere este umbral será cancelada por el motor
de base de datos con:

    django.db.utils.OperationalError:
        canceling statement due to statement timeout

Este error es capturado en views.py para retornar la respuesta degradada.

Flujo normal (happy path, < 100ms):
    [Request] → get_project_report(project_id) → [QuerySet ORM] → [datos] → [JSON]
                                                  ↓
                                            [Guardar Report en BD]

Flujo de fallo de timeout (> 1000ms):
    [Request] → get_project_report(project_id) → [QuerySet ORM] → OperationalError
                                                                            ↓
                                                                  views.py → graceful_failure

Nota sobre el ASR:
    El escenario define:
      - 100ms: tiempo normal de procesamiento
      - 300ms adicionales como presupuesto máximo para manejo de falla
      - 400ms: tiempo de respuesta total máximo
    El timeout de 1000ms es el máximo de BD; la respuesta debe ocurrir
    en < 400ms total (detección + respuesta degradada).
===========================================================================
"""

import logging
import time
from datetime import datetime

from django.db import connection, OperationalError, DatabaseError
from django.db.models import Count, Sum, Case, When, F, Max
from django.utils import timezone

from .models import Project, Report

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

    Esta función encapsula la consulta usando Django ORM y está diseñada
    para ser consumida por la vista. Si la DB falla (timeout, conexión caída),
    propaga la excepción para que la capa de vista aplique la táctica de Degradation.

    También guarda un registro de Report en BD para auditoría.

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
        # Obtener el proyecto usando Django ORM
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            logger.warning("Proyecto no encontrado: project_id=%d", project_id)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            # Registrar reporte de fallo
            Report.objects.create(
                project_id=project_id,
                status="failed",
                failure_reason="connection_error",
                response_time_ms=elapsed_ms,
                error_message=f"Proyecto {project_id} no encontrado",
            )
            
            return {
                "project_id": project_id,
                "found": False,
                "data": None,
                "query_time_ms": round(elapsed_ms, 2),
            }

        # Calcular estadísticas de tareas usando ORM
        task_stats = project.tasks.aggregate(
            total_tasks=Count("id"),
            completed_tasks=Sum(
                Case(When(completed=True, then=1), default=0)
            ),
            last_activity=Max("updated_at"),
        )

        total_tasks = task_stats["total_tasks"] or 0
        completed_tasks = task_stats["completed_tasks"] or 0
        completion_percentage = (
            (100.0 * completed_tasks / total_tasks)
            if total_tasks > 0
            else 0.0
        )
        last_activity = task_stats["last_activity"]

        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Consulta completada en %.2fms para project_id=%d",
            elapsed_ms,
            project_id,
        )

        # Construir respuesta exitosa
        response_data = {
            "project_id": project.id,
            "found": True,
            "data": {
                "project_name": project.name,
                "project_status": project.status,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": round(completion_percentage, 2),
                "last_activity": last_activity.isoformat() if last_activity else None,
            },
            "query_time_ms": round(elapsed_ms, 2),
        }

        # Guardar reporte en BD (éxito)
        Report.objects.create(
            project=project,
            status="success",
            failure_reason="none",
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_percentage=round(completion_percentage, 2),
            response_time_ms=elapsed_ms,
            query_time_ms=elapsed_ms,
            last_activity=last_activity,
        )

        return response_data

    except OperationalError as db_err:
        # ------------------------------------------------------------------
        # TÁCTICA 2: TIMEOUT — captura del error de PostgreSQL
        # ------------------------------------------------------------------
        # PostgreSQL lanza OperationalError con "canceling statement due to
        # statement timeout" cuando se exceden los 1000ms configurados.
        # Lo reenvolvemos en ServiceUnavailableError para que views.py
        # pueda distinguirlo semánticamente y retornar la respuesta degradada.
        # ------------------------------------------------------------------
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.error(
            "Timeout o error operacional en consulta DB (%.2fms): %s",
            elapsed_ms,
            db_err,
        )

        # Intentar guardar el fallo en BD (si es posible)
        try:
            Report.objects.create(
                project_id=project_id,
                status="degraded",
                failure_reason="timeout",
                response_time_ms=elapsed_ms,
                error_message=str(db_err)[:255],
            )
        except Exception as report_err:
            logger.warning("No se pudo guardar reporte de fallo: %s", report_err)

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

        # Intentar guardar el fallo en BD (si es posible)
        try:
            Report.objects.create(
                project_id=project_id,
                status="failed",
                failure_reason="connection_error",
                response_time_ms=elapsed_ms,
                error_message=str(db_err)[:255],
            )
        except Exception as report_err:
            logger.warning("No se pudo guardar reporte de fallo: %s", report_err)

        raise ServiceUnavailableError(
            "Error inesperado al consultar la base de datos"
        ) from db_err
