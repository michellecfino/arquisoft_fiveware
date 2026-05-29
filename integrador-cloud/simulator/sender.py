import os
import logging
import requests
from typing import Dict, Any

# Configuración básica de logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("SenderService")

class ConsumptionSender:
    """
    Clase encargada de transmitir los datos de consumo de nube normalizados a la API de agregación.
    
    ENCAPSULATE:
    Esta clase encapsula toda la infraestructura y lógica de comunicación HTTP (timeouts, cabeceras, reintentos y
    el manejo exhaustivo de excepciones de red), aislando al simulador principal de los detalles de red y protocolos.
    """

    def __init__(self):
        # Obtener el endpoint desde las variables de entorno, usando el valor provisto por defecto si no está definido
        self.url = os.getenv("AGGREGATOR_URL", "http://44.203.209.23:8002/api/ingest/")
        self.timeout = 5.0  # Timeout de 5 segundos para evitar bloqueos prolongados (Alta disponibilidad)
        
        # Estructura contractual de datos requerida para el agregador
        self._required_fields = {
            "id_empresa": (int,),
            "id_area": (int,),
            "id_proyecto": (int,),
            "nombre_servicio": (str,),
            "costo": (float, int),
            "moneda": (str,),
            "anio": (int,),
            "mes": (int,)
        }

    def _validate_contract(self, data: Dict[str, Any]) -> bool:
        """
        Valida que el diccionario cumpla estrictamente con el contrato del agregador.
        """
        if not isinstance(data, dict):
            logger.error("Data contract validation failed: payload is not a dictionary.")
            return False
            
        for field, expected_types in self._required_fields.items():
            if field not in data:
                logger.error(f"Data contract validation failed: missing required field '{field}'.")
                return False
            
            value = data[field]
            if not isinstance(value, expected_types):
                logger.error(
                    f"Data contract validation failed for '{field}': "
                    f"expected types {expected_types}, got {type(value).__name__}."
                )
                return False
                
        return True

    def send(self, provider_name: str, data: Dict[str, Any]) -> bool:
        """
        Envía un payload de consumo normalizado a través de un HTTP POST.
        
        Valida el contrato en frontera y maneja timeouts y errores de red.
        """
        # Validación en frontera (Defensive design táctico para producción)
        if not self._validate_contract(data):
            logger.error(f"Data contract verification rejected sending payload for provider {provider_name}.")
            return False

        logger.info(f"Sending {provider_name} consumption...")
        
        try:
            # Enviar el POST request con cabecera JSON y payload normalizado
            response = requests.post(
                self.url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            # Verificar si la respuesta posee un código HTTP exitoso (2xx)
            if response.status_code in [200, 201]:
                logger.info(f"Response: {response.status_code} OK")
                return True
            else:
                logger.error(
                    f"Response: {response.status_code} Invalid Status Code. "
                    f"Payload sent: {data} - Response body: {response.text}"
                )
                return False
                
        except requests.exceptions.Timeout:
            # Manejo del escenario: Timeout (el servidor está sobrecargado o lento)
            logger.error(f"Timeout error: The server at {self.url} failed to respond within {self.timeout}s.")
            return False
            
        except requests.exceptions.ConnectionError:
            # Manejo del escenario: Conexión rechazada o DNS inaccesible (servidor caído)
            logger.error(f"Connection rejected: Could not reach the aggregator server at {self.url}.")
            return False
            
        except requests.exceptions.RequestException as e:
            # Captura de cualquier otra anomalía en el envío HTTP
            logger.error(f"HTTP request failed unexpectedly: {e}")
            return False
