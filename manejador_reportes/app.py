import pika
import json
import time
from flask import Flask, request, jsonify
from database import get_db_connection
import os

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME', 'postgres')
RABBIT_HOST = os.getenv('RABBIT_HOST','rabbitmq')
RABBIT_USER = os.getenv('RABBIT_USER', 'guest')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'guest')

def conectar_con_reintento():
    while True:
        try:
            print(" [*] Intentando conectar a RabbitMQ...")
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
            )
            return connection
        except Exception:
            print(" [!] RabbitMQ no listo. Reintentando en 10 segundos...")
            time.sleep(10)   

def enviar_a_cola(mensaje):
    try:
        # Usamos la lógica de reintento también aquí para que no falle el request
        connection = conectar_con_reintento()
        channel = connection.channel()
        channel.queue_declare(queue='cola_notificaciones', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='cola_notificaciones',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        return True
    except Exception as e:
        print(f"Error enviando a cola: {e}")
        return False

@app.route('/reporte-mensual', methods=['POST'])
def obtener_reporte():
    data = request.get_json()
    empresa_id = data.get('empresa_id')
    proyecto_id = data.get('proyecto_id')
    anio = 2026
    mes = 3
    
    email_usuario = data.get('email', 'usuario@ejemplo.com') # Simulando el destino

    datos_notificacion = {
        "empresa_id": empresa_id,
        "proyecto_id": proyecto_id,
        "email": email_usuario,
        "anio": anio,
        "mes": mes,
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
            "message": "Rabbitmq no respondió"}), 500
        
        
     
       
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
