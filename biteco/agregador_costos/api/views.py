from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pymongo

client = pymongo.MongoClient('mongodb://172.31.23.83:27017/')
db = client['biteco_db']
resumenes = db['resumen_mensual_costos']

@csrf_exempt
def ingest(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            resumenes.update_one(
                {
                    'id_empresa': data['id_empresa'],
                    'id_proyecto': data['id_proyecto'],
                    'anio': data['anio'],
                    'mes': data['mes']
                },
                {
                    '$inc': {'costo_total': data['costo'], 'cantidad_registros': 1},
                    '$set': {'moneda': data['moneda']}
                },
                upsert=True
            )
            
            return JsonResponse({'ok': True, 'message': 'Resumen actualizado'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST required'}, status=400)

def resumenes_list(request):
    proyecto = request.GET.get('proyecto')
    anio = request.GET.get('anio')
    mes = request.GET.get('mes')
    
    query = {}
    if proyecto:
        query['id_proyecto'] = int(proyecto)
    if anio:
        query['anio'] = int(anio)
    if mes:
        query['mes'] = int(mes)
    
    data = list(resumenes.find(query, {'_id': 0}))
    return JsonResponse({'total': len(data), 'data': data})

def health(request):
    try:
        client.admin.command('ping')
        return JsonResponse({'status': 'ok', 'database': 'connected'})
    except:
        return JsonResponse({'status': 'ok', 'database': 'disconnected'}, status=500)
