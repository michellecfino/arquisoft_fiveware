"""
views.py — Capa de Presentación: endpoint de reporte de proyectos.

===========================================================================
TÁCTICA 3: DEGRADATION (Bass et al.)
===========================================================================
Si el sistema detecta que la base de datos NO está disponible (Táctica 1:
Heartbeat retorna False) O si la consulta lanza una excepción de Timeout
(Táctica 2), la vista NO retorna un error 500 ni colapsa. En su lugar,
retorna una respuesta "degradada" pero funcional:

    HTTP 200 (por diseño del ASR — el sistema sigue respondiendo)
    {
        "status": "graceful_failure",
        "message": "No pudimos obtener tus datos, por favor reintenta",
        "project_id": <id>,
        "data": null
    }

Esto garantiza que la experiencia del usuario empresarial sea predecible
y el sistema permanezca disponible según el ASR, con un tiempo total de
respuesta máximo de 400ms (100ms normal + 300ms budget de falla).

Flujo completo:
    ┌─────────────────────────────────────────────────────────────────┐
    │  GET /api/reports/<project_id>/                                  │
    └─────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────┐
    │  cache.get('db_available')          │  ← Táctica 1: Heartbeat
    └──────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │ False / None         │ True
        ▼                     ▼
    [DEGRADED]        get_project_report()    ← Táctica 2: Timeout (en services.py)
    (graceful)             │
                  ┌────────┴────────┐
                  │ OK              │ ServiceUnavailableError
                  ▼                 ▼
            [200 + data]       [DEGRADED]     ← Táctica 3: Degradation
                               (graceful)
===========================================================================
"""

import logging
import time

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from .heartbeat import get_db_availability
from .services import get_project_report, ServiceUnavailableError

logger = logging.getLogger("disponibilidad.views")

# ---------------------------------------------------------------------------
# Constantes de respuesta
# ---------------------------------------------------------------------------

#: Mensaje de usuario final para el escenario de falla (definido en el ASR)
GRACEFUL_FAILURE_MESSAGE = "Servicio temporalmente no disponible, por favor reintente"

#: Status string para identificar respuestas degradadas en los logs/tests
STATUS_SUCCESS = "success"
STATUS_GRACEFUL_FAILURE = "graceful_failure"


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

class ProjectReportView(View):
    """
    Endpoint que retorna el reporte de disponibilidad de un proyecto.

    Usa :class:`django.views.View` (no DRF ``APIView``) para combinar sin fricción
    :func:`render` (HTML) y :class:`JsonResponse` (API) según negociación simple
    del cliente.

    Implementa las tres tácticas de Bass:
      1. Consulta el Heartbeat (caché) para fallo rápido (Táctica 1)
      2. Delega a services.py que aplica Timeout de 200ms (Táctica 2)
      3. Retorna respuesta degradada en cualquier falla (Táctica 3)

    Los navegadores (``Accept`` con ``text/html``) reciben HTML; clientes API
    pueden forzar JSON con ``?format=json`` o enviando ``Accept: application/json``.

    URL: GET /api/reports/<project_id>/
    """

    def get(self, request, project_id: int | None = None):
        """
        Maneja la solicitud HTTP GET para obtener el reporte de un proyecto.

        El tiempo total de respuesta garantizado por el ASR es <= 400ms:
          - Ruta feliz: < 100ms (consulta normal)
          - Ruta de falla: < 400ms (detección + respuesta degradada)
        """
        if project_id is None:
            try:
                project_id = int(request.GET.get("project_id", "1"))
            except ValueError:
                project_id = 1

        request_start = time.monotonic()
        logger.info("Request recibido: GET /api/reports/%d/", project_id)

        # ------------------------------------------------------------------
        # PASO 1 — TÁCTICA 1: Consultar el Heartbeat
        # ------------------------------------------------------------------
        # Leer el estado de la DB desde HeartbeatState (memoria local).
        # Si el Heartbeat ha detectado que la DB no está disponible, evitamos
        # ejecutar la consulta y retornamos inmediatamente la respuesta degradada.
        # Esto reduce la latencia de fallo < 50ms (solo lectura de estado en memoria).
        # ------------------------------------------------------------------
        db_is_available, failure_reason = get_db_availability()

        if not db_is_available:
            elapsed = (time.monotonic() - request_start) * 1000
            logger.warning(
                "Heartbeat indica DB no disponible — degradación (%.2fms desde inicio)",
                elapsed,
            )
            # TÁCTICA 3: DEGRADATION — fallo detectado por Heartbeat
            if self._prefers_json(request):
                return self._graceful_failure_response(
                    project_id=project_id,
                    elapsed_ms=elapsed,
                    reason="heartbeat",
                )
            return render(
                request,
                "error_degradacion.html",
                {
                    "project_id": project_id,
                    "response_time_ms": round(elapsed, 2),
                },
                status=200,
            )

        # ------------------------------------------------------------------
        # PASO 2 — TÁCTICA 2: Ejecutar consulta con Timeout
        # ------------------------------------------------------------------
        # La consulta tiene un statement_timeout de 200ms a nivel de DB
        # (configurado en settings.py). Si se excede, services.py lanza
        # ServiceUnavailableError y lo capturamos aquí para degradar.
        # ------------------------------------------------------------------
        try:
            report_data = get_project_report(project_id=project_id)
            elapsed = (time.monotonic() - request_start) * 1000

            logger.info(
                "Consulta exitosa para project_id=%d en %.2fms",
                project_id,
                elapsed,
            )

            # Respuesta exitosa: HTML para browser, JSON para clientes API
            if not self._prefers_json(request):
                return render(
                    request,
                    "project_report.html",
                    {
                        "project_id": project_id,
                        "found": report_data.get("found"),
                        "data": report_data.get("data"),
                        "response_time_ms": round(elapsed, 2),
                    },
                    status=200,
                )
            return JsonResponse(
                {
                    "status": STATUS_SUCCESS,
                    "project_id": project_id,
                    "data": report_data.get("data"),
                    "found": report_data.get("found"),
                    "response_time_ms": round(elapsed, 2),
                },
                status=200,
            )

        except ServiceUnavailableError as svc_err:
            # ------------------------------------------------------------------
            # TÁCTICA 3: DEGRADATION — fallo detectado por Timeout/Error DB
            # ------------------------------------------------------------------
            # La consulta excedió el timeout de 200ms o la DB tiene un error.
            # En lugar de propagar un 500, retornamos la respuesta degradada
            # garantizando que el usuario recibe una respuesta en < 400ms.
            # ------------------------------------------------------------------
            elapsed = (time.monotonic() - request_start) * 1000
            logger.error(
                "ServiceUnavailableError para project_id=%d (%.2fms): %s",
                project_id,
                elapsed,
                svc_err,
            )
            if not self._prefers_json(request):
                return render(
                    request,
                    "error_degradacion.html",
                    {
                        "project_id": project_id,
                        "response_time_ms": round(elapsed, 2),
                    },
                    status=200,
                )
            return self._graceful_failure_response(
                project_id=project_id,
                elapsed_ms=elapsed,
                reason="timeout",
            )

        except Exception as unexpected_err:  # noqa: BLE001
            # Captura defensiva para errores no anticipados (también degrada)
            elapsed = (time.monotonic() - request_start) * 1000
            logger.exception(
                "Error inesperado para project_id=%d (%.2fms): %s",
                project_id,
                elapsed,
                unexpected_err,
            )
            if not self._prefers_json(request):
                return render(
                    request,
                    "error_degradacion.html",
                    {
                        "project_id": project_id,
                        "response_time_ms": round(elapsed, 2),
                    },
                    status=200,
                )
            return self._graceful_failure_response(
                project_id=project_id,
                elapsed_ms=elapsed,
                reason="unexpected",
            )

    # ------------------------------------------------------------------
    # Negociación HTML / JSON (front-first: por defecto HTML)
    # ------------------------------------------------------------------

    @staticmethod
    def _prefers_json(request) -> bool:
        """
        True si conviene servir JSON (curl/Postman). Por defecto servimos HTML
        para priorizar display en browser y cumplir el ASR con degradación en HTML.
        """
        if request.GET.get("format") == "json":
            return True
        if request.GET.get("format") == "html":
            return False
        accept = (request.headers.get("Accept") or "").lower()
        return "application/json" in accept

    # ------------------------------------------------------------------
    # TÁCTICA 3: Helper de respuesta degradada
    # ------------------------------------------------------------------

    @staticmethod
    def _graceful_failure_response(
        project_id: int,
        elapsed_ms: float,
        reason: str,
    ) -> JsonResponse:
        """
        Construye la respuesta de degradación definida en el ASR.

        El mensaje es exactamente el especificado en el requisito:
            "No pudimos obtener tus datos, por favor reintenta"

        El status HTTP es 200 porque el sistema SIGUE FUNCIONANDO (degradado,
        no caído). Los clientes pueden diferenciar usando el campo 'status'.

        Args:
            project_id:  ID del proyecto solicitado.
            elapsed_ms:  Tiempo transcurrido hasta la detección del fallo.
            reason:      'heartbeat' | 'timeout' | 'unexpected'

        Returns:
            JsonResponse con status HTTP 200 y cuerpo de graceful_failure.
        """
        return JsonResponse(
            {
                "status": STATUS_GRACEFUL_FAILURE,
                "message": GRACEFUL_FAILURE_MESSAGE,
                "project_id": project_id,
                "data": None,
                "failure_reason": reason,
                "response_time_ms": round(elapsed_ms, 2),
            },
            status=200,  # El sistema responde — solo degrada el contenido
        )


# ---------------------------------------------------------------------------
# Vista de health check (opcional, para load balancers y monitoreo externo)
# ---------------------------------------------------------------------------

class HealthCheckView(View):
    """
    Endpoint de health check para load balancers y sistemas de monitoreo externos.

    Retorna el estado actual del sistema incluyendo el estado del Heartbeat.
    URL: GET /health/
    """

    def get(self, request):
        db_available = cache.get(DB_AVAILABLE_CACHE_KEY, default=None)
        body = {
            "service": "disponibilidad-asr",
            "healthy": db_available is True,
            "db_available": db_available,
            "heartbeat_key": DB_AVAILABLE_CACHE_KEY,
        }
        strict = request.GET.get("strict") == "1"
        if strict:
            status_code = 200 if db_available is True else 503
        else:
            # ALB + Kong: estado 200 aun si la RDS falla la app degradada sigue sirviendo
            status_code = 200

        return JsonResponse(body, status=status_code)
