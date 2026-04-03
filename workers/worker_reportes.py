#Encontré que esta librería es una implementación de RabbitMQ
import pika 
import json
import time
from database_config import get_db_connection # Asumiendo que tu código anterior está en este archivo

def procesar_notificacion(ch, method, properties, body):
    data = json.loads(body)
    print(f" Reporte recibido {data['proyecto_id']}")
    
    
    time.sleep(1)
    print(f"Notificación recibida correo enviado a la cola.")
    
    # Avisa a Rabbit que elimine el mensaje de la cola
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_consumidor():
    rabbit_host = os.getenv("RABBITMQ_HOST", "localhost")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
    channel = connection.channel()

    # durable=True para que los mensajes no se pierdan si se cae el servidor
    channel.queue_declare(queue='cola_notificaciones_reporte', durable=True)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='cola_notificaciones_reporte', on_message_callback=procesar_notificacion)

    print(' [*] Worker activo. Esperando reportes... (CTRL+C para salir)')
    channel.start_consuming()

if __name__ == '__main__':
    iniciar_consumidor()