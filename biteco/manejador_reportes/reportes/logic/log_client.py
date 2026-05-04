import logging

logger = logging.getLogger(__name__)

def registrar_accion(user_id, accion, detalle=""):
    """
    En el experimento de confidencialidad no hay manejador de logs separado.
    Registramos solo en el log local de Django.
    """
    try:
        logger.info(f"AUDIT | user={user_id} | accion={accion} | detalle={detalle}")
    except Exception as e:
        pass