import pika
import json
import time
import sys
import os

# 1. Configuración
RABBIT_HOST = os.getenv('RABBIT_HOST','rabbitmq')
RABBIT_USER = os.getenv('RABBIT_USER', 'guest')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'guest')

def enviar_correo_simulado(data):
    email = data.get('email')
    proyecto = data.get('proyecto_id')
    print(f" [-->] Enviando reporte del proyecto {proyecto} a {email}...", flush=True)
    time.sleep(1) 
    print(f" [OK] Correo enviado exitosamente a {email}", flush=True)
    return True

def callback(ch, method, properties, body):
    print(f" [x] Mensaje recibido: {body.decode()}", flush=True)
    try:
        data = json.loads(body)
        if enviar_correo_simulado(data):
            ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f" [!] Error procesando mensaje: {e}")

def iniciar_worker():
    # EL SECRETO: Un bucle que no deja morir al worker
    while True:
        try:
            print(" [*] Intentando conectar a RabbitMQ...", flush=True)
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
            )
            channel = connection.channel()
            channel.queue_declare(queue='cola_notificaciones', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='cola_notificaciones', on_message_callback=callback)

            print(' [V] Worker de Email iniciado. Esperando mensajes...')
            channel.start_consuming()

        except Exception as e:
            print(f" [!] Error de conexión ({e}). Reintentando en 10 segundos...")
            time.sleep(10) # Espera antes de volver a intentar al inicio del bucle

if __name__ == '__main__':
    iniciar_worker()