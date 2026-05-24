# agregacion/views.py (solo para recibir datos, sin exponer via Kong)
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import ResumenMensualCosto, DetalleServicio
from datetime import datetime

@csrf_exempt
@require_http_methods(["POST"])
def ingest_data(request):
    """Endpoint interno para recibir datos (NO expuesto por Kong)"""
    try:
        payload = json.loads(request.body)
        
        with transaction.atomic():
            # Actualizar resumen
            resumen, created = ResumenMensualCosto.objects.update_or_create(
                id_empresa=payload['id_empresa'],
                id_area=payload['id_area'],
                id_proyecto=payload['id_proyecto'],
                anio=payload['anio'],
                mes=payload['mes'],
                defaults={
                    'moneda': payload['moneda'],
                    'costo_total': models.F('costo_total') + payload['costo'],
                    'cantidad_registros': models.F('cantidad_registros') + 1,
                    'ultima_actualizacion': datetime.now()
                }
            )
            
            # Actualizar detalle
            detalle, created = DetalleServicio.objects.update_or_create(
                id_resumen=resumen.id_resumen,
                nombre_servicio=payload['nombre_servicio'],
                defaults={
                    'costo_total': models.F('costo_total') + payload['costo'],
                    'cantidad_registros': models.F('cantidad_registros') + 1,
                    'moneda': payload['moneda'],
                    'ultima_actualizacion': datetime.now()
                }
            )
            
            return JsonResponse({
                "status": "success",
                "id_resumen": resumen.id_resumen,
                "costo_total": resumen.costo_total
            }, status=201)
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)