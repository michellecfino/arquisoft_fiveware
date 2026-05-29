import random
from typing import Dict, Any
from plugins.base import CloudProviderPlugin

class AzurePlugin(CloudProviderPlugin):
    """
    Plugin de simulación para Microsoft Azure.
    
    ENCAPSULATE:
    Este plugin encapsula el conocimiento de los servicios de Azure (App Service, Azure SQL, Functions)
    y su lógica de simulación.
    """

    def __init__(self):
        self.services = ["App Service", "Azure SQL", "Functions"]

    def generate_consumption(self) -> Dict[str, Any]:
        service = random.choice(self.services)
        cost = round(random.uniform(0.01, 600.00), 2)
        
        return {
            "id_empresa": 1,
            "id_area": 10,
            "id_proyecto": 100,
            "nombre_servicio": f"Azure - {service}",
            "costo": cost,
            "moneda": "USD",
            "anio": 2026,
            "mes": 5
        }
