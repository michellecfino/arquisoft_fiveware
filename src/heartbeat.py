"""
heartbeat.py — Táctica 1: Heartbeat (Bass et al.)

===========================================================================
TÁCTICA 1: HEARTBEAT
===========================================================================
Esta táctica consiste en un proceso que, a intervalos regulares (cada 1s),
emite un "latido" verificando si un componente crítico (la base de datos)
está disponible. El resultado se almacena en caché (Redis) como la llave
'db_available'. La vista en views.py consulta este estado antes de ejecutar
cualquier consulta real, permitiendo el fallo anticipado (fail fast) y
la respuesta degradada (táctica de Degradación).

Flujo:
  [Hilo Heartbeat] ── cada 1s ──► [Prueba conexión DB] ──► [caché Redis]
                                                                  │
                                              ┌───────────────────┘
                                              ▼
  [Request HTTP] ──► [views.py] ──► [cache.get('db_available')]
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

import django
from django.core.cache import cache

logger = logging.getLogger("disponibilidad.heartbeat")

# ---------------------------------------------------------------------------
# Constantes de configuración
# ---------------------------------------------------------------------------

#: Intervalo entre verificaciones de salud de la DB (en segundos)
HEARTBEAT_INTERVAL_SECONDS: float = 1.0

#: Tiempo máximo de espera para la prueba de conexión (en segundos)
#: Debe ser bastante menor que el statement_timeout de 1000ms de la app
HEARTBEAT_PROBE_TIMEOUT_SECONDS: float = 0.30  # 300ms

#: Llave de caché donde se almacena el estado de la DB
DB_AVAILABLE_CACHE_KEY: str = "db_available"

#: TTL de la llave en caché: si el heartbeat muere, expira en 5s → failsafe
DB_CACHE_TTL_SECONDS: int = 5


class HeartbeatService:
    """
    Servicio de Heartbeat que verifica la conectividad a la base de datos.

    Ejecuta un hilo daemon que sondea la DB cada HEARTBEAT_INTERVAL_SECONDS
    y persiste el resultado en caché Redis para que la capa de vistas pueda
    tomar decisiones de degradación sin ejecutar consultas costosas.
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
        """
        Persiste el estado de disponibilidad de la DB en caché Redis.

        El TTL de DB_CACHE_TTL_SECONDS garantiza que si el hilo de heartbeat
        muere inesperadamente, la llave expira y views.py puede tomar
        la decisión conservadora de asumir que la DB no está disponible.
        """
        try:
            cache.set(DB_AVAILABLE_CACHE_KEY, is_available, timeout=DB_CACHE_TTL_SECONDS)
            logger.info(
                "Heartbeat → cache['%s'] = %s",
                DB_AVAILABLE_CACHE_KEY,
                is_available,
            )
        except Exception as cache_exc:  # noqa: BLE001
            logger.error("Heartbeat — no se pudo actualizar la caché: %s", cache_exc)

    # ------------------------------------------------------------------
    # Loop principal del hilo
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Bucle principal que ejecuta probe + cache update cada 1 segundo."""
        logger.info(
            "HeartbeatService iniciado — verificando DB cada %.1fs",
            HEARTBEAT_INTERVAL_SECONDS,
        )

        while not self._stop_event.is_set():
            is_available = self._probe_database()
            self._update_cache(is_available)

            # Esperar el intervalo configurado (soporta stop_event para salida limpia)
            self._stop_event.wait(timeout=HEARTBEAT_INTERVAL_SECONDS)

        logger.info("HeartbeatService detenido.")

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


# ---------------------------------------------------------------------------
# Punto de entrada directo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
    os.environ["RUN_HEARTBEAT_MAIN"] = "1"
    django.setup()

    service = HeartbeatService()
    service.start()

    # Mantener el proceso vivo en ejecución standalone
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
        logger.info("Heartbeat detenido por el usuario.")
