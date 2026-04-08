import json
import os
import smtplib
import time
from email.message import EmailMessage

import requests
from django.db import connection


def consumir_cola_y_enviar():
    queue_url = (
        f"http://{os.getenv('RABBITMQ_HOST')}:{os.getenv('RABBITMQ_API_PORT')}"
        f"/api/queues/%2F/{os.getenv('RABBITMQ_QUEUE')}/get"
    )

    auth = (os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASSWORD"))

    while True:
        response = requests.post(
            queue_url,
            auth=auth,
            json={
                "count": 10,
                "ackmode": "ack_requeue_false",
                "encoding": "auto",
                "truncate": 50000
            },
            timeout=30,
        )
        response.raise_for_status()
        mensajes = response.json()

        if not mensajes:
            time.sleep(2)
            continue

        for mensaje in mensajes:
            payload = json.loads(mensaje["payload"])
            enviar_correo(payload)


def enviar_correo(payload):
    email = EmailMessage()
    email["Subject"] = f"Reporte generado #{payload['id_reporte']}"
    email["From"] = os.getenv("SMTP_FROM")
    email["To"] = payload["correo_destino"]
    email.set_content(
        f"{payload['mensaje']}\n\n"
        f"Acceso: {payload['url_acceso']}\n"
    )

    try:
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as smtp:
            smtp.send_message(email)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE nucleo.notificaciones
                SET estado = 'Enviada',
                    fecha_envio = NOW(),
                    smtp_message_id = %s,
                    intentos = intentos + 1,
                    error_detalle = NULL
                WHERE id_notificacion = %s
                """,
                [email.get("Message-ID"), payload["id_notificacion"]],
            )
    except Exception as exc:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE nucleo.notificaciones
                SET estado = 'Fallida',
                    intentos = intentos + 1,
                    error_detalle = %s
                WHERE id_notificacion = %s
                """,
                [str(exc), payload["id_notificacion"]],
            )