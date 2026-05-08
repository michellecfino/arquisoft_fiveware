"""
apps.py — Configuración de la AppConfig de Django.

Al usar AppConfig.ready(), arrancamos el HeartbeatService automáticamente
cuando Django carga la aplicación, sin necesidad de un comando aparte.

Táctica 1 (Heartbeat): El hilo daemon se inicia aquí al arrancar el servidor.
"""

import logging

from django.apps import AppConfig

logger = logging.getLogger("disponibilidad.heartbeat")


class SrcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src"
    verbose_name = "Disponibilidad ASR"

    def ready(self) -> None:
        """
        Hook de Django ejecutado una sola vez cuando la app está lista.

        Inicia el HeartbeatService en un hilo daemon para que comience
        a verificar la DB cada 1 segundo y persistir el estado en caché.

        Nota: Se omite el inicio en management commands (migrate, shell, etc.)
        y en procesos de reloader de Django para evitar hilos duplicados.
        """
        import os
        import sys

        # Evitar doble inicio en el reloader de Django (RUN_MAIN env var)
        # y en comandos de gestión que no necesitan el heartbeat
        is_management_command = (
            len(sys.argv) > 1 and sys.argv[1] in ("migrate", "shell", "collectstatic", "test")
        )
        is_reloader_child = os.environ.get("RUN_MAIN") != "true"

        if is_management_command or is_reloader_child:
            return

        from .heartbeat import HeartbeatService

        service = HeartbeatService()
        service.start()
        logger.info("HeartbeatService iniciado desde AppConfig.ready()")
