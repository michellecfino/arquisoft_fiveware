from django.db import models


class ResumenMensualCosto(models.Model):
    id_resumen = models.BigAutoField(primary_key=True)
    id_empresa = models.IntegerField()
    id_area = models.IntegerField()
    id_proyecto = models.IntegerField()
    anio = models.IntegerField()
    mes = models.IntegerField()
    moneda = models.CharField(max_length=3)
    costo_total = models.DecimalField(max_digits=14, decimal_places=4)
    cantidad_registros = models.IntegerField()
    ultima_actualizacion = models.DateTimeField()

    class Meta:
        db_table = 'reportes"."resumen_mensual_costos'
        managed = False


class DetalleServicio(models.Model):
    id_detalle = models.BigAutoField(primary_key=True)
    id_resumen = models.BigIntegerField()
    nombre_servicio = models.CharField(max_length=100)
    cantidad_registros = models.IntegerField()
    costo_total = models.DecimalField(max_digits=14, decimal_places=4)
    moneda = models.CharField(max_length=3)
    ultima_actualizacion = models.DateTimeField()

    class Meta:
        db_table = 'reportes"."detalle_servicio'
        managed = False


class ReporteGenerado(models.Model):
    id_reporte = models.BigAutoField(primary_key=True)
    id_resumen = models.BigIntegerField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reportes"."reportes_generados'
        managed = False