import requests
import os

AUDIT_URL = os.getenv("AUDIT_URL", "http://manejador_logs:8001/audit/log/")

def registrar_accion(user_id, action):
    payload = {
        "user_id": user_id,
        "service": "reportes",
        "action": action
    }

    try:
        requests.post(AUDIT_URL, json=payload)
    except Exception as e:
        print("Error enviando log:", e)