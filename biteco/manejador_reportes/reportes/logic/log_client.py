from reportes.services.logs_client import registrar_evento

LOG_SERVICE_URL = "http://TU-IP-PRIVADA-LOGS:8000/audit/log/"

def registrar_evento(user_id, user_role, action):
    try:
        registrar_evento(
            user_id,
            user_role,
            f"Generó reporte proyecto={id_proyecto}, periodo={mes}/{anio}"
        )
    except Exception:
        # no romper flujo por logs
        pass
