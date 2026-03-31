from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import psycopg2
import os
import pika

@csrf_exempt
def generar_reporte(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            empresa_id = data['empresa_id']
            proyecto_id = data['proyecto_id']
            anio = data['anio']
            mes = data['mes']

            # Consulta optimizada (tabla agregada)
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS")
            )
            cur = conn.cursor()

            cur.execute("""
                SELECT costo_total
                FROM analytics.resumen_mensual_costos
                WHERE empresa_id = %s
                  AND proyecto_id = %s
                  AND anio = %s
                  AND mes = %s
            """, (empresa_id, proyecto_id, anio, mes))

            resultado = cur.fetchone()

            cur.close()
            conn.close()

            # Publicar evento
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='localhost')
            )
            channel = connection.channel()

            channel.queue_declare(queue='cola_notificaciones_reporte')

            mensaje = json.dumps({
                "empresa_id": empresa_id,
                "proyecto_id": proyecto_id,
                "costo": resultado[0] if resultado else 0
            })

            channel.basic_publish(
                exchange='',
                routing_key='cola_notificaciones_reporte',
                body=mensaje
            )

            connection.close()

            return JsonResponse({
                "status": "ok",
                "costo": resultado[0] if resultado else 0
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)