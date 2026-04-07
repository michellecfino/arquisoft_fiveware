import pika
import json
import time  
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('DB_NAME', 'choco_reportes')
RABBIT_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBIT_USER = os.getenv('RABBIT_USER', 'guest')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'guest')

def conectar_con_reintento():
    """Intenta conectar a RabbitMQ hasta que tenga éxito"""
    while True:
        try:
            print(" [*] Intentando conectar a RabbitMQ...", flush=True)
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
            )
            return connection
        except Exception as e:
            print(f" [!] RabbitMQ no listo ({e}). Reintentando en 10 segundos...", flush=True)
            time.sleep(10)   

def enviar_a_cola(mensaje):
    """Publica el evento en RabbitMQ usando la conexión con reintento"""
    try:
        connection = conectar_con_reintento()
        channel = connection.channel()
        
        channel.queue_declare(queue='cola_notificaciones', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='cola_notificaciones',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        connection.close()
        return True
    except Exception as e:

        print(f"Error enviando a RabbitMQ: {e}", flush=True)
        return False

@app.route('/reporte-mensual', methods=['POST'])
def obtener_reporte():
    data = request.get_json()
    if not data:
        return jsonify({"status": "fail", "message": "No data provided"}), 400
        
    empresa_id = data.get('empresa_id')
    proyecto_id = data.get('proyecto_id')
    email_usuario = data.get('email', 'usuario@ejemplo.com')

    datos_notificacion = {
        "empresa_id": empresa_id,
        "proyecto_id": proyecto_id,
        "email": email_usuario,
        "anio": 2026,
        "mes": 3,
        "mensaje": f"Tu reporte del proyecto {proyecto_id} está listo."
    }

    fue_encolado = enviar_a_cola(datos_notificacion)

    if fue_encolado:
        return jsonify({
            "status": "success",
            "message": "Reporte procesado. La notificación se enviará en breve."
        }), 200
    else:
        return jsonify({
            "status": "fail",
            "message": "RabbitMQ no respondió"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)