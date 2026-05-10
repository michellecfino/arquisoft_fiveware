import requests
import os

LOG_SERVICE_URL = os.getenv("LOG_SERVICE_URL", "http://10.0.2.215:8002/audit/log/")

def registrar_evento(user_id, user_role, action):
    """Envía un log al servicio de auditoría"""
    try:
        payload = {
            "user_id": str(user_id),
            "role": user_role,
            "action": action,
            "service": "reportes"
        }
        
        response = requests.post(
            LOG_SERVICE_URL,
            headers={
                "Content-Type": "application/json",
                "X-Internal-Token": "super-secret"
            },
            json=payload,
            timeout=2
        )
        
        if response.status_code != 200:
            print(f"[LOG] Error: {response.status_code}")
            
    except Exception as e:
        print(f"[LOG] Error al enviar log: {e}")

def registrar_accion(user_id, action, details=""):
    """Alias para registrar_evento con más parámetros"""
    registrar_evento(user_id, "USER", f"{action}: {details}")
