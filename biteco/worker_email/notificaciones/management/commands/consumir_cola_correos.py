from django.core.management.base import BaseCommand
from notificaciones.logic.notificaciones_logic import consumir_cola_y_enviar


class Command(BaseCommand):
    help = "Consume mensajes de RabbitMQ y envia correos"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Consumidor AMQP iniciado"))
        consumir_cola_y_enviar()