from django.db import transaction
from datetime import datetime
from decimal import Decimal
from ..models import Consumo, ResumenMensual, MetricasDashboard

class AgregacionService:
    
    @transaction.atomic
    def procesar_consumo(self, datos):
        """
        Procesa un nuevo consumo y actualiza agregaciones
        Implementa COMPUTED PATTERN
        """
        # 1. Guardar consumo original
        consumo = Consumo.objects.create(
            id_empresa=datos['id_empresa'],
            id_area=datos['id_area'],
            id_proyecto=datos['id_proyecto'],
            nombre_servicio=datos['nombre_servicio'],
            costo=datos['costo'],
            moneda=datos['moneda'],
            anio=datos['anio'],
            mes=datos['mes'],
            fecha_consumo=datetime(datos['anio'], datos['mes'], 1),
            procesado=True
        )
        
        # 2. Actualizar resumen mensual
        id_compuesto = f"{datos['id_empresa']}|{datos['id_area']}|{datos['id_proyecto']}|{datos['anio']}|{datos['mes']}"
        
        resumen, created = ResumenMensual.objects.get_or_create(
            _id=id_compuesto,
            defaults={
                'id_empresa': datos['id_empresa'],
                'id_area': datos['id_area'],
                'id_proyecto': datos['id_proyecto'],
                'anio': datos['anio'],
                'mes': datos['mes'],
                'moneda': datos['moneda'],
                'costo_total': Decimal('0'),
                'cantidad_registros': 0,
                'servicios': []
            }
        )
        
        resumen.actualizar_con_consumo(consumo)
        
        # 3. Actualizar métricas del dashboard
        self.actualizar_metricas_dashboard(datos['anio'], datos['mes'])
        
        return {
            'success': True,
            'consumo_id': str(consumo.id),
            'resumen_id': resumen._id,
            'message': 'Consumo procesado exitosamente'
        }
    
    def actualizar_metricas_dashboard(self, anio, mes):
        """Actualiza métricas pre-calculadas del dashboard (COMPUTED PATTERN)"""
        resumenes = ResumenMensual.objects.filter(anio=anio, mes=mes)
        
        if not resumenes.exists():
            return
        
        # Calcular métricas globales
        total_empresas = resumenes.values('id_empresa').distinct().count()
        total_proyectos = resumenes.values('id_proyecto').distinct().count()
        costo_total_general = sum(float(r.costo_total) for r in resumenes)
        total_transacciones = sum(r.cantidad_registros for r in resumenes)
        
        # Calcular top proyectos
        proyectos_dict = {}
        for resumen in resumenes:
            key = f"{resumen.id_empresa}|{resumen.id_proyecto}"
            if key not in proyectos_dict:
                proyectos_dict[key] = {
                    'id_proyecto': resumen.id_proyecto,
                    'id_empresa': resumen.id_empresa,
                    'costo_total': Decimal('0'),
                    'total_registros': 0
                }
            proyectos_dict[key]['costo_total'] += resumen.costo_total
            proyectos_dict[key]['total_registros'] += resumen.cantidad_registros
        
        top_proyectos = sorted(
            proyectos_dict.values(),
            key=lambda x: x['costo_total'],
            reverse=True
        )[:5]
        
        for proyecto in top_proyectos:
            proyecto['porcentaje_del_total'] = (float(proyecto['costo_total']) / costo_total_general * 100) if costo_total_general > 0 else 0
        
        # Calcular costos por servicio
        servicios_dict = {}
        for resumen in resumenes:
            for servicio in resumen.servicios:
                nombre = servicio['nombre_servicio']
                if nombre not in servicios_dict:
                    servicios_dict[nombre] = {
                        'nombre_servicio': nombre,
                        'costo_total': Decimal('0'),
                        'cantidad_registros': 0
                    }
                servicios_dict[nombre]['costo_total'] += servicio['costo_total']
                servicios_dict[nombre]['cantidad_registros'] += servicio['cantidad_registros']
        
        costos_por_servicio = []
        for servicio in servicios_dict.values():
            porcentaje = (float(servicio['costo_total']) / costo_total_general * 100) if costo_total_general > 0 else 0
            costos_por_servicio.append({
                'nombre_servicio': servicio['nombre_servicio'],
                'costo_total': servicio['costo_total'],
                'cantidad_registros': servicio['cantidad_registros'],
                'porcentaje_del_total': porcentaje
            })
        
        costos_por_servicio.sort(key=lambda x: x['costo_total'], reverse=True)
        
        # Guardar métricas
        MetricasDashboard.objects.update_or_create(
            _id=f"DASH|{anio}|{mes}",
            defaults={
                'anio': anio,
                'mes': mes,
                'total_empresas': total_empresas,
                'total_proyectos': total_proyectos,
                'costo_total_general': costo_total_general,
                'total_transacciones': total_transacciones,
                'top_proyectos': top_proyectos,
                'costos_por_servicio': costos_por_servicio
            }
        )
    
    def consultar_resumenes(self, filtros=None):
        """Consulta resúmenes usando índices compuestos (ATTRIBUTE PATTERN)"""
        query = {}
        if filtros:
            if filtros.get('id_empresa'):
                query['id_empresa'] = filtros['id_empresa']
            if filtros.get('id_proyecto'):
                query['id_proyecto'] = filtros['id_proyecto']
            if filtros.get('anio'):
                query['anio'] = filtros['anio']
            if filtros.get('mes'):
                query['mes'] = filtros['mes']
        
        return ResumenMensual.objects.filter(**query).order_by('-anio', '-mes')
    
    def obtener_metricas_dashboard(self, anio, mes):
        """Obtiene métricas pre-calculadas"""
        try:
            return MetricasDashboard.objects.get(_id=f"DASH|{anio}|{mes}")
        except MetricasDashboard.DoesNotExist:
            self.actualizar_metricas_dashboard(anio, mes)
            return MetricasDashboard.objects.get(_id=f"DASH|{anio}|{mes}")
    
    def obtener_series_tiempo(self, id_proyecto, meses=12):
        """Obtiene series de tiempo para gráficos"""
        from django.db.models import Q
        
        resumenes = ResumenMensual.objects.filter(
            id_proyecto=id_proyecto
        ).order_by('-anio', '-mes')[:meses]
        
        return [
            {
                'periodo': f"{r.anio}-{str(r.mes).zfill(2)}",
                'costo_total': r.costo_total,
                'cantidad_registros': r.cantidad_registros,
                'servicios': r.servicios
            }
            for r in reversed(resumenes)
        ]

agregacion_service = AgregacionService()