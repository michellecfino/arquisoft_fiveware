import pika
import json
import time
import sys
import os


RABBIT_HOST = os.getenv('RABBIT_HOST')
RABBIT_USER = os.getenv('RABBIT_USER', 'admin_biteco')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'password123')
def enviar_correo_simulado(data):
    """Aquí es donde conectarías con Amazon SES o Mailtrap"""
    email = data.get('email')
    proyecto = data.get('proyecto_id')
    
    print(f" [-->] Enviando reporte del proyecto {proyecto} a {email}...")
    
    # Simulamos la latencia de red de un servicio de correo (0.5 a 1 seg)
    time.sleep(0.5) 
    
    print(f" [OK] Correo enviado exitosamente a {email}")
    return True

def callback(ch, method, properties, body):
    """Función que se ejecuta cada vez que llega un mensaje a la cola"""
    print(f" [x] Mensaje recibido: {body.decode()}")
    
    try:
        # Convertir el cuerpo del mensaje (JSON) a diccionario Python
        data = json.loads(body)
        
        # Intentar enviar el correo
        exito = enviar_correo_simulado(data)
        
        if exito:
            # Confirmamos a RabbitMQ que procesamos el mensaje
            # Si no enviamos esto, RabbitMQ vuelve a poner el mensaje en la cola
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
    except Exception as e:
        print(f" [!] Error procesando mensaje: {e}")
        # En caso de error crítico, no damos el ACK para que otro worker lo intente
        # o lo mandamos a una cola de errores (Dead Letter Exchange)

def iniciar_worker():
    try:
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
        )
        channel = connection.channel()

        # Nos aseguramos de que la cola exista
        channel.queue_declare(queue='cola_notificaciones', durable=True)

        # IMPORTANTE PARA ESCALABILIDAD:
        # No le des más de 1 mensaje a este worker hasta que termine el anterior.
        # Esto permite que si tienes 4 workers, la carga se reparta perfecta.
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue='cola_notificaciones', on_message_callback=callback)

        print(' [*] Worker de Email iniciado. Esperando mensajes. Para salir: CTRL+C')
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print(" [!] No se pudo conectar a RabbitMQ. ¿Está encendido el servidor?")
    except KeyboardInterrupt:
        print(" [!] Worker detenido por el usuario.")
        sys.exit(0)

if __name__ == '__main__':
    iniciar_worker()
