"""
heartbeat.py — Táctica 1: Heartbeat (Bass et al.)

===========================================================================
TÁCTICA 1: HEARTBEAT (Refactorizada sin Redis)
===========================================================================
Verificación periódica de disponibilidad de BD usando almacenamiento
en memoria local (HeartbeatState) en lugar de Redis.

Flujo:
  [Hilo Heartbeat] ── cada 1s ──► [Prueba conexión DB] ──► [Memoria local]
                                                               │
                                  ┌───────────────────────────┘
                                  ▼
  [Request HTTP] ──► [views.py] ──► [get_db_availability()]
                                              │
                              ┌───── True ────┴──── False ─────┐
                              ▼                                 ▼
                    [Ejecuta consulta DB]             [graceful_failure]
===========================================================================

Uso:
    # Iniciar como proceso daemon (en manage.py o como comando de gestión):
    from src.heartbeat import HeartbeatService
    hb = HeartbeatService()
    hb.start()   # inicia el hilo daemon

    # O ejecutar directamente desde CLI:
    python -m src.heartbeat
"""

import logging
import threading
import time
from datetime import datetime

import django

logger = logging.getLogger("disponibilidad.heartbeat")

# ---------------------------------------------------------------------------
# Constantes de configuración
# ---------------------------------------------------------------------------

#: Intervalo entre verificaciones de salud de la DB (en segundos)
HEARTBEAT_INTERVAL_SECONDS: float = 1.0

#: Tiempo máximo de espera para la prueba de conexión (en segundos)
#: Debe ser bastante menor que el statement_timeout de 1000ms de la app
HEARTBEAT_PROBE_TIMEOUT_SECONDS: float = 0.30  # 300ms


# ---------------------------------------------------------------------------
# Estado global del Heartbeat (reemplaza a Redis)
# ---------------------------------------------------------------------------

class HeartbeatState:
    """
    Almacena el estado de disponibilidad de la BD en memoria local con Lock.

    Reemplaza la funcionalidad anterior de caché Redis.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._is_available: bool = True
        self._last_probe_time: datetime | None = None
        self._last_failure_reason: str | None = None

    def set_status(
        self,
        is_available: bool,
        failure_reason: str | None = None,
    ) -> None:
        """Actualiza el estado de disponibilidad."""
        with self._lock:
            self._is_available = is_available
            self._last_probe_time = datetime.now()
            self._last_failure_reason = failure_reason

    def get_status(self) -> tuple[bool, str | None]:
        """Retorna (is_available, failure_reason)."""
        with self._lock:
            return self._is_available, self._last_failure_reason

    def get_last_probe_time(self) -> datetime | None:
        """Retorna la hora del último sondeo."""
        with self._lock:
            return self._last_probe_time


# Instancia global compartida
_heartbeat_state = HeartbeatState()


def get_db_availability() -> tuple[bool, str | None]:
    """API pública para consultar disponibilidad de BD."""
    return _heartbeat_state.get_status()


class HeartbeatService:
    """
    Servicio de Heartbeat que verifica la conectividad a la base de datos.

    Ejecuta un hilo daemon que sondea la DB cada HEARTBEAT_INTERVAL_SECONDS
    y persiste el resultado en HeartbeatState (memoria local).
    """

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Probe — verificación de salud
    # ------------------------------------------------------------------

    def _probe_database(self) -> bool:
        """
        Intenta ejecutar una consulta mínima contra la base de datos.

        Returns:
            True  — la DB está disponible y respondió en tiempo.
            False — la DB no está disponible (timeout, error de conexión, etc.)
        """
        try:
            from django.db import connection, connections

            # Forzar apertura de nueva conexión para evitar usar una ya caída
            conn = connections["default"]
            conn.ensure_connection()

            with conn.cursor() as cursor:
                # Consulta mínima que no toca datos reales; solo prueba el socket
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            if result and result[0] == 1:
                logger.debug("Heartbeat ✓ — DB disponible")
                return True

        except Exception as exc:  # noqa: BLE001
            # Capturamos cualquier excepción: timeout, connection refused, etc.
            logger.warning("Heartbeat ✗ — DB no disponible: %s", exc)

        return False

    def _update_cache(self, is_available: bool) -> None:
        """state(self, is_available: bool) -> None:
        """Persiste el estado de disponibilidad de la DB en memoria."""
        try:
            failure_reason = None if is_available else "connection_error"
            _heartbeat_state.set_status(is_available, failure_reason)
            logger.info(
                "Heartbeat → estado actualizado: is_available=%s",
                is_available,
            )
        except Exception as state_exc:  # noqa: BLE001
            logger.error("Heartbeat — no se pudo actualizar el estado: %s", stat
    # ------------------------------------------------------------------
    # Loop principal del hilo
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Bucle principal que ejecuta probe + cache update cada 1 segundo."""
        logger.info(
            "HeartbeatService iniciado — verificando DB cada %.1fs",
            HEARTBEAT_INTERVAL_SECONDS,
        )

        while not self._stop_event.is_set():state update cada 1 segundo."""
        logger.info(
            "HeartbeatService iniciado — verificando DB cada %.1fs",
            HEARTBEAT_INTERVAL_SECONDS,
        )

        while not self._stop_event.is_set():
            is_available = self._probe_database()
            self._update_stat
    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Inicia el hilo daemon de heartbeat."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("HeartbeatService ya está en ejecución.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="heartbeat-db",
            daemon=True,  # Se detiene automáticamente cuando el proceso principal termina
        )
        self._thread.start()
        logger.info("Hilo '%s' iniciado.", self._thread.name)

    def stop(self) -> None:
        """Detiene el hilo de heartbeat limpiamente."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self) -> bool:
        """Retorna True si el hilo de heartbeat está activo."""
        return self._thread is not None and self._thread.is_alive()
