"""
models.py — Modelos de datos para reportes de disponibilidad.

Almacenan en PostgreSQL los proyectos, tareas y reportes generados.
No usa Redis; todo persiste en la BD.
"""

from django.db import models
from django.utils import timezone


class Project(models.Model):
    """Representa un proyecto siendo monitorizado."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("active", "Activo"), ("inactive", "Inactivo")],
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def __str__(self):
        return f"{self.name} ({self.status})"


class Task(models.Model):
    """Representa una tarea dentro de un proyecto."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class Report(models.Model):
    """
    Reporte de disponibilidad generado para un proyecto.

    Almacena los resultados de cada consulta (éxito, fallo, latencia, etc.)
    para análisis posterior y auditoría.
    """

    STATUS_CHOICES = [
        ("success", "Éxito"),
        ("degraded", "Degradado"),
        ("failed", "Fallo"),
    ]

    REASON_CHOICES = [
        ("none", "Ninguno"),
        ("heartbeat", "Heartbeat"),
        ("timeout", "Timeout"),
        ("connection_error", "Error de Conexión"),
        ("unknown", "Desconocido"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="reports"
    )

    # Estado del reporte
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="success")

    # Razón de fallo (si aplica)
    failure_reason = models.CharField(
        max_length=50, choices=REASON_CHOICES, default="none"
    )

    # Datos del reporte
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)

    # Métricas de latencia
    response_time_ms = models.FloatField(default=0.0)  # Tiempo total de respuesta
    query_time_ms = models.FloatField(null=True, blank=True)  # Tiempo de consulta BD

    # Información adicional
    error_message = models.TextField(blank=True, null=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"Report {self.project.name} - {self.status} ({self.created_at})"


class HeartbeatStatus(models.Model):
    """
    Estado actual del heartbeat (reemplaza a Redis).

    Almacena en BD si la base de datos está disponible,
    permitiendo que views.py consulte este estado rápidamente
    sin ejecutar una consulta costosa.
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="heartbeat_status"
    )

    is_available = models.BooleanField(default=True)
    last_probe_time = models.DateTimeField(auto_now=True)
    last_failure_reason = models.CharField(
        max_length=255, blank=True, null=True
    )

    class Meta:
        verbose_name = "Estado Heartbeat"
        verbose_name_plural = "Estados Heartbeat"

    def __str__(self):
        status = "✓ Disponible" if self.is_available else "✗ No disponible"
        return f"{self.project.name} - {status}"
