from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services.agregacion_service import agregacion_service

@api_view(['POST'])
def recibir_consumo(request):
    """Endpoint para recibir datos normalizados del integrador"""
    try:
        datos = request.data
        
        # Validaciones
        required_fields = ['id_empresa', 'id_area', 'id_proyecto', 
                          'nombre_servicio', 'costo', 'moneda', 'anio', 'mes']
        
        for field in required_fields:
            if field not in datos:
                return Response(
                    {'error': f'Campo requerido: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        resultado = agregacion_service.procesar_consumo(datos)
        return Response(resultado, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def consultar_resumenes(request):
    """Consultar resúmenes con filtros"""
    filtros = {}
    
    if request.GET.get('id_empresa'):
        filtros['id_empresa'] = int(request.GET.get('id_empresa'))
    if request.GET.get('id_proyecto'):
        filtros['id_proyecto'] = int(request.GET.get('id_proyecto'))
    if request.GET.get('anio'):
        filtros['anio'] = int(request.GET.get('anio'))
    if request.GET.get('mes'):
        filtros['mes'] = int(request.GET.get('mes'))
    
    resumenes = agregacion_service.consultar_resumenes(filtros)
    
    # Convertir a lista para serializar
    data = []
    for r in resumenes:
        data.append({
            'id_empresa': r.id_empresa,
            'id_proyecto': r.id_proyecto,
            'anio': r.anio,
            'mes': r.mes,
            'costo_total': float(r.costo_total),
            'cantidad_registros': r.cantidad_registros,
            'costo_promedio': float(r.costo_promedio),
            'moneda': r.moneda,
            'servicios': r.servicios
        })
    
    return Response({
        'total': len(data),
        'data': data
    })

@api_view(['GET'])
def obtener_metricas_dashboard(request):
    """Obtener métricas para dashboard"""
    anio = int(request.GET.get('anio'))
    mes = int(request.GET.get('mes'))
    
    metricas = agregacion_service.obtener_metricas_dashboard(anio, mes)
    
    return Response({
        'anio': metricas.anio,
        'mes': metricas.mes,
        'total_empresas': metricas.total_empresas,
        'total_proyectos': metricas.total_proyectos,
        'costo_total_general': float(metricas.costo_total_general),
        'total_transacciones': metricas.total_transacciones,
        'top_proyectos': metricas.top_proyectos,
        'costos_por_servicio': metricas.costos_por_servicio
    })

@api_view(['GET'])
def health_check(request):
    """Health check del servicio"""
    return Response({
        'status': 'healthy',
        'service': 'agregador-costos',
        'database': 'mongodb'
    })