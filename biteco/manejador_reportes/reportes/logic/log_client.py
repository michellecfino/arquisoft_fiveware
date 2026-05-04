import requests
import os

AUDIT_URL = os.getenv("AUDIT_URL", "http://manejador_logs:8001/audit/log/")

def registrar_accion(user_id, action, metadata=""):
    mensaje_completo = f"[{action}] - {metadata}"
    
    payload = {
        "level": "INFO" if "ERROR" not in action else "ERROR",
        "message": f"User: {user_id} | {mensaje_completo}"
    }

    try:
        requests.post(AUDIT_URL, json=payload, timeout=3)
    except Exception as e:
        print(f"Error enviando log: {e}")
