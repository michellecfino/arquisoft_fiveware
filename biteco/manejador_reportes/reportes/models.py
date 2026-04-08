from django.db import models

class Proyecto(models.Model):
    id_proyecto = models.AutoField(primary_key=True)
    id_empresa = models.IntegerField()
    id_area = models.IntegerField()
    nombre = models.CharField(max_length=150)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'nucleo"."proyectos'

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    id_empresa = models.IntegerField()
    nombre = models.CharField(max_length=120)
    correo = models.CharField(max_length=150)
    rol = models.CharField(max_length=40)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'nucleo"."usuarios'

class Region(models.Model):
    id_region = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'nube"."regiones'

class ServicioCloud(models.Model):
    id_servicio_cloud = models.BigAutoField(primary_key=True)
    identificador_cuenta_cloud = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'nube"."servicios_cloud'

class RegistroConsumo(models.Model):
    id_registro_consumo = models.BigAutoField(primary_key=True)
    id_proyecto = models.IntegerField()
    id_servicio_cloud = models.BigIntegerField()
    id_region = models.IntegerField(null=True)
    fecha_consumo = models.DateField()
    grupo_recurso = models.CharField(max_length=150, null=True)
    costo = models.DecimalField(max_digits=14, decimal_places=4)
    moneda = models.CharField(max_length=10)
    id_recurso_crudo = models.TextField()

    class Meta:
        managed = False
        db_table = 'nube"."registros_consumo'

class ReporteGenerado(models.Model):
    id_reporte = models.BigAutoField(primary_key=True)
    id_empresa = models.IntegerField()
    id_area = models.IntegerField()
    id_proyecto = models.IntegerField()
    id_usuario = models.IntegerField()
    anio = models.IntegerField()
    mes = models.IntegerField()
    moneda = models.CharField(max_length=10)
    total_costo = models.DecimalField(max_digits=14, decimal_places=4)
    cantidad_registros = models.IntegerField()
    request_id = models.CharField(max_length=100, unique=True)
    instancia_origen = models.CharField(max_length=100)
    fecha_generacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'reportes"."reportes_generados'

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