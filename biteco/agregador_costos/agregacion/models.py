from django.db import models

class Consumo(models.Model):
    id_empresa = models.IntegerField()
    id_area = models.IntegerField()
    id_proyecto = models.IntegerField()
    nombre_servicio = models.CharField(max_length=100)
    costo = models.DecimalField(max_digits=14, decimal_places=4)
    moneda = models.CharField(max_length=3)
    anio = models.IntegerField()
    mes = models.IntegerField()
    fecha_consumo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'consumos'
        indexes = [
            models.Index(fields=['id_proyecto', 'anio', 'mes']),
        ]

class ResumenMensual(models.Model):
    id_empresa = models.IntegerField()
    id_area = models.IntegerField()
    id_proyecto = models.IntegerField()
    anio = models.IntegerField()
    mes = models.IntegerField()
    moneda = models.CharField(max_length=3)
    costo_total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    cantidad_registros = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'resumenes'
        unique_together = ['id_empresa', 'id_area', 'id_proyecto', 'anio', 'mes']
        indexes = [
            models.Index(fields=['id_proyecto', 'anio', 'mes']),
        ]
