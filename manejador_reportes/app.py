import pika
import json
from flask import Flask, request, jsonify
from database import get_db_connection

app = Flask(__name__)

RABBIT_HOST = 'rabbitmq'
RABBIT_USER = 'admin_biteco'
RABBIT_PASS = 'password123'

def enviar_a_cola(mensaje):
    """Función para publicar el evento en RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
        )
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
        print(f"Error conectando a RabbitMQ: {e}")
        return False

@app.route('/reporte-mensual', methods=['POST'])
def obtener_reporte():
    data = request.get_json()
    empresa_id = data.get('empresa_id')
    proyecto_id = data.get('proyecto_id')
    email_usuario = data.get('email', 'usuario@ejemplo.com') # Simulando el destino

    anio = 2026
    mes = 3
    datos_notificacion = {
        "empresa_id": empresa_id,
        "proyecto_id": proyecto_id,
        "anio": anio,
        "mes": mes,
        "email": email_usuario,
        "mensaje": f"Tu reporte del proyecto {proyecto_id} está listo."
    }

    fue_encolado = enviar_a_cola(datos_notificacion)

    if fue_encolado:
        return jsonify({
            "status": "success",
            "message": "Reporte procesado. La notificación se enviará en breve."
        }), 200
    else:
        # 💡 CAMBIO TEMPORAL PARA MICHELLE: 
        # Si RabbitMQ falla, igual mostramos éxito en la terminal para debuguear
        print(f"⚠️ RabbitMQ no está disponible, pero recibí: {datos_notificacion}")
        
        return jsonify({
            "status": "success_local", 
            "message": "API funcionando, pero RabbitMQ está apagado."
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
