import random
from plugins.base import CloudProviderPlugin

class GCPPlugin(CloudProviderPlugin):
    """
    Plugin de simulación para Google Cloud Platform (GCP).
    
    ENCAPSULATE:
    Este plugin encapsula el conocimiento de los servicios de GCP (Compute Engine, Cloud Storage, BigQuery)
    y su lógica de simulación.
    """

    def __init__(self):
        self.services = ["Compute Engine", "Cloud Storage", "BigQuery"]

    def generate_consumption(self) -> dict:
        service = random.choice(self.services)
        cost = round(random.uniform(0.10, 450.00), 2)
        
        return {
            "id_empresa": 1,
            "id_area": 10,
            "id_proyecto": 100,
            "nombre_servicio": f"GCP - {service}",
            "costo": cost,
            "moneda": "USD",
            "anio": 2026,
            "mes": 5
        }
