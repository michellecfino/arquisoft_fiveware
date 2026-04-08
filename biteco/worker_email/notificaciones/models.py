from django.db import models

class Notificacion(models.Model):
    id_notificacion = models.BigAutoField(primary_key=True)
    id_usuario = models.IntegerField()
    id_reporte = models.BigIntegerField()
    correo_destino = models.CharField(max_length=150)
    fecha_creacion = models.DateTimeField()
    fecha_envio = models.DateTimeField(null=True)
    estado = models.CharField(max_length=30)
    broker_message_id = models.CharField(max_length=200, null=True)
    smtp_message_id = models.CharField(max_length=200, null=True)
    intentos = models.IntegerField()
    mensaje = models.TextField()
    url_acceso = models.TextField(null=True)
    error_detalle = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'nucleo"."notificaciones'