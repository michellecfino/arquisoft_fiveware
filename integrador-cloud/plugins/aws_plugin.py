import random
from plugins.base import CloudProviderPlugin

class AWSPlugin(CloudProviderPlugin):
    """
    Plugin de simulación para Amazon Web Services (AWS).
    
    ENCAPSULATE:
    Este plugin encapsula el conocimiento de los servicios de AWS (EC2, S3, Lambda) y
    su lógica específica de simulación y generación de costos.
    """

    def __init__(self):
        self.services = ["EC2", "S3", "Lambda"]

    def generate_consumption(self) -> dict:
        # Selección aleatoria de servicio
        service = random.choice(self.services)
        
        # Generar costo simulado realista (de $0.05 a $500.00)
        cost = round(random.uniform(0.05, 500.00), 2)
        
        # Estructura del JSON normalizado según los requerimientos
        return {
            "id_empresa": 1,
            "id_area": 10,
            "id_proyecto": 100,
            "nombre_servicio": f"AWS - {service}",
            "costo": cost,
            "moneda": "USD",
            "anio": 2026,
            "mes": 5
        }
