from django.db import models
from djongo import models as djongo_models

class Consumo(models.Model):
    """
    Documento de consumo original
    Cada transacción individual
    """
    # ATTRIBUTE PATTERN: Campos indexados para consultas rápidas
    id_empresa = models.IntegerField(db_index=True)
    id_area = models.IntegerField(db_index=True)
    id_proyecto = models.IntegerField(db_index=True)
    nombre_servicio = models.CharField(max_length=100)
    costo = models.DecimalField(max_digits=14, decimal_places=4)
    moneda = models.CharField(max_length=3)
    
    anio = models.IntegerField(db_index=True)
    mes = models.IntegerField(db_index=True)
    fecha_consumo = models.DateTimeField()
    
    timestamp = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'consumos'
        # ATTRIBUTE PATTERN: Índice compuesto
        indexes = [
            models.Index(fields=['id_empresa', 'id_area', 'id_proyecto', 'anio', 'mes'], 
                        name='idx_consumo_compuesto'),
            models.Index(fields=['id_proyecto', 'anio', 'mes'], 
                        name='idx_consumo_proyecto_periodo'),
            models.Index(fields=['anio', 'mes'], name='idx_consumo_periodo'),
        ]
    
    def __str__(self):
        return f"Consumo {self.id_proyecto} - {self.nombre_servicio} - {self.costo}"


class ResumenMensual(models.Model):
    """
    COMPUTED PATTERN: Datos pre-agregados y pre-calculados
    ATTRIBUTE PATTERN: Llave compuesta como _id
    """
    # ATTRIBUTE PATTERN: ID Compuesto
    _id = models.CharField(max_length=100, primary_key=True)
    
    # Atributos para consultas
    id_empresa = models.IntegerField(db_index=True)
    id_area = models.IntegerField()
    id_proyecto = models.IntegerField(db_index=True)
    anio = models.IntegerField(db_index=True)
    mes = models.IntegerField(db_index=True)
    moneda = models.CharField(max_length=3)
    
    # COMPUTED PATTERN: Métricas pre-calculadas
    costo_total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    cantidad_registros = models.IntegerField(default=0)
    costo_promedio = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    costo_minimo = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    costo_maximo = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    
    # Array de servicios (embedded documents)
    servicios = djongo_models.ArrayField(
        model_container='agregacion.models.DetalleServicio',
        default=list
    )
    
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'resumenes_mensuales'
        # ATTRIBUTE PATTERN: Múltiples índices compuestos
        indexes = [
            models.Index(fields=['id_empresa', 'id_proyecto', 'anio', 'mes'], 
                        name='idx_resumen_empresa_proyecto'),
            models.Index(fields=['id_proyecto', 'anio', 'mes'], 
                        name='idx_resumen_proyecto_periodo'),
            models.Index(fields=['anio', 'mes'], name='idx_resumen_periodo'),
            models.Index(fields=['costo_total'], name='idx_resumen_costo'),
        ]
    
    def save(self, *args, **kwargs):
        # Generar ID compuesto automáticamente
        if not self._id:
            self._id = f"{self.id_empresa}|{self.id_area}|{self.id_proyecto}|{self.anio}|{self.mes}"
        super().save(*args, **kwargs)
    
    def actualizar_con_consumo(self, consumo):
        """Actualiza el resumen con un nuevo consumo"""
        # Actualizar métricas generales
        self.costo_total += consumo.costo
        self.cantidad_registros += 1
        self.costo_promedio = self.costo_total / self.cantidad_registros
        
        if self.costo_minimo == 0 or consumo.costo < self.costo_minimo:
            self.costo_minimo = consumo.costo
        if consumo.costo > self.costo_maximo:
            self.costo_maximo = consumo.costo
        
        # Actualizar detalle de servicios
        servicio_existente = None
        for i, servicio in enumerate(self.servicios):
            if servicio['nombre_servicio'] == consumo.nombre_servicio:
                servicio_existente = i
                break
        
        if servicio_existente is not None:
            self.servicios[servicio_existente]['cantidad_registros'] += 1
            self.servicios[servicio_existente]['costo_total'] += consumo.costo
            self.servicios[servicio_existente]['costo_promedio'] = \
                self.servicios[servicio_existente]['costo_total'] / self.servicios[servicio_existente]['cantidad_registros']
        else:
            self.servicios.append({
                'nombre_servicio': consumo.nombre_servicio,
                'cantidad_registros': 1,
                'costo_total': consumo.costo,
                'costo_promedio': consumo.costo,
                'moneda': consumo.moneda
            })
        
        self.version += 1
        self.save()
    
    def __str__(self):
        return f"Resumen {self.id_proyecto} - {self.anio}/{self.mes} - ${self.costo_total}"


class DetalleServicio(models.Model):
    """
    Documento embebido para detalle de servicios
    """
    nombre_servicio = models.CharField(max_length=100)
    cantidad_registros = models.IntegerField(default=0)
    costo_total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    costo_promedio = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    moneda = models.CharField(max_length=3)
    
    class Meta:
        abstract = True


class MetricasDashboard(models.Model):
    """
    COMPUTED PATTERN: Métricas pre-calculadas para dashboards
    """
    _id = models.CharField(max_length=50, primary_key=True)
    
    anio = models.IntegerField(db_index=True)
    mes = models.IntegerField(db_index=True)
    
    # Métricas globales
    total_empresas = models.IntegerField(default=0)
    total_proyectos = models.IntegerField(default=0)
    costo_total_general = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total_transacciones = models.IntegerField(default=0)
    
    # Top proyectos (embedded)
    top_proyectos = djongo_models.ArrayField(
        model_container='agregacion.models.TopProyecto',
        default=list
    )
    
    # Costos por servicio (embedded)
    costos_por_servicio = djongo_models.ArrayField(
        model_container='agregacion.models.CostoServicio',
        default=list
    )
    
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'metricas_dashboard'
        indexes = [
            models.Index(fields=['anio', 'mes'], name='idx_metricas_periodo'),
        ]
    
    def save(self, *args, **kwargs):
        if not self._id:
            self._id = f"DASH|{self.anio}|{self.mes}"
        super().save(*args, **kwargs)


class TopProyecto(models.Model):
    """Documento embebido para top proyectos"""
    id_proyecto = models.IntegerField()
    id_empresa = models.IntegerField()
    costo_total = models.DecimalField(max_digits=14, decimal_places=4)
    total_registros = models.IntegerField()
    porcentaje_del_total = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        abstract = True


class CostoServicio(models.Model):
    """Documento embebido para costos por servicio"""
    nombre_servicio = models.CharField(max_length=100)
    costo_total = models.DecimalField(max_digits=14, decimal_places=4)
    cantidad_registros = models.IntegerField()
    porcentaje_del_total = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        abstract = True