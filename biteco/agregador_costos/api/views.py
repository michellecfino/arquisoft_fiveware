from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['biteco_db']
resumenes = db['resumenes']
consumos = db['consumos']

@csrf_exempt
def ingest(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            consumo = {
                'id_empresa': data['id_empresa'],
                'id_proyecto': data['id_proyecto'],
                'nombre_servicio': data['nombre_servicio'],
                'costo': data['costo'],
                'moneda': data['moneda'],
                'anio': data['anio'],
                'mes': data['mes']
            }
            consumos.insert_one(consumo)
            
            resumenes.update_one(
                {
                    'id_empresa': data['id_empresa'],
                    'id_proyecto': data['id_proyecto'],
                    'anio': data['anio'],
                    'mes': data['mes']
                },
                {
                    '$inc': {'costo_total': data['costo'], 'cantidad': 1},
                    '$set': {'moneda': data['moneda']}
                },
                upsert=True
            )
            
            return JsonResponse({'ok': True, 'message': 'Consumo registrado'})
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
