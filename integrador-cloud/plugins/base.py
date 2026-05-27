from abc import ABC, abstractmethod

class CloudProviderPlugin(ABC):
    """
    Clase abstracta base que actúa como el contrato común para todos los proveedores cloud.
    
    ========================================================================================
    OBJETIVOS ARQUITECTÓNICOS IMPLEMENTADOS:
    
    1. ABSTRACT COMMON SERVICES (Abstracción de Servicios Comunes):
       - Definimos un contrato estandarizado para la obtención de datos de consumo de nube.
       - La interfaz obliga a que cada proveedor, sin importar sus peculiaridades internas,
         implemente el método 'generate_consumption' retornando una estructura homogénea.
         
    2. ENCAPSULATE (Encapsulamiento):
       - Cada plugin de proveedor encapsula toda la lógica de su simulación específica, la selección
         de sus servicios propios y la forma en que computa sus costos.
       - El flujo principal del simulador interactúa únicamente a través de esta interfaz abstracta, 
         desconociendo los detalles de implementación interna de cada nube.
         
    3. MODIFICABILIDAD (Modificabilidad ASR):
       - Al utilizar un cargador de plugins y un contrato abstractificado, el sistema permite
         añadir nuevos proveedores (por ejemplo, Oracle Cloud u OpenStack) simplemente creando 
         un nuevo archivo en esta carpeta que implemente esta interfaz.
       - Esto se logra sin alterar una sola línea del simulador principal o de la lógica de envío.
    ========================================================================================
    """

    @abstractmethod
    def generate_consumption(self) -> dict:
        """
        Genera y retorna un diccionario normalizado que simula el consumo de la nube.
        
        El formato del JSON normalizado retornado debe ser estrictamente:
        {
            "id_empresa": int,
            "id_area": int,
            "id_proyecto": int,
            "nombre_servicio": str,
            "costo": float,
            "moneda": str,
            "anio": int,
            "mes": int
        }
        """
        pass
