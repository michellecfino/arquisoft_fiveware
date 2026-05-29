import random
from typing import Dict, Any
from plugins.base import CloudProviderPlugin

class OCIPlugin(CloudProviderPlugin):
    """
    Plugin de simulación dummy para Oracle Cloud Infrastructure (OCI).
    
    Este plugin sirve como demostración práctica del ASR de Modificabilidad.
    Al agregarse a la carpeta 'plugins/', es detectado e inicializado automáticamente
    por el cargador de plugins sin alterar ninguna otra línea del código del sistema.
    """

    def __init__(self):
        self.services = ["Compute Instance", "Object Storage", "Autonomous DB"]

    def generate_consumption(self) -> Dict[str, Any]:
        service = random.choice(self.services)
        cost = round(random.uniform(0.50, 300.00), 2)
        
        return {
            "id_empresa": 1,
            "id_area": 10,
            "id_proyecto": 100,
            "nombre_servicio": f"OCI - {service}",
            "costo": cost,
            "moneda": "USD",
            "anio": 2026,
            "mes": 5
        }
