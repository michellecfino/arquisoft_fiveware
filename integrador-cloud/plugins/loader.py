import os
import importlib
import pkgutil
import inspect
from plugins.base import CloudProviderPlugin

def load_plugins() -> list:
    """
    Carga dinámicamente todos los plugins en el directorio 'plugins/' que implementen
    la clase abstracta CloudProviderPlugin.
    
    MODIFICABILIDAD (ASR):
    Este cargador implementa la reflexión en tiempo de ejecución. Escanea todos los archivos
    en la carpeta 'plugins/', los importa dinámicamente utilizando importlib y pkgutil, 
    e inspecciona sus clases para encontrar aquellas que sean subclases de CloudProviderPlugin.
    Añadir un proveedor nuevo no requiere registrarlo aquí; basta con soltar su archivo .py en esta carpeta.
    """
    plugins = []
    
    # Obtener el directorio actual del loader (plugins/)
    plugins_dir = os.path.dirname(__file__)
    
    # pkgutil.iter_modules requiere una lista de directorios para buscar módulos
    for _, module_name, is_pkg in pkgutil.iter_modules([plugins_dir]):
        # Omitimos el contrato base y el cargador en sí mismos
        if module_name in ["base", "loader"]:
            continue
            
        try:
            # Importación dinámica del módulo dentro del paquete plugins
            module = importlib.import_module(f"plugins.{module_name}")
            
            # Buscar elementos dentro del módulo que sean subclases de CloudProviderPlugin y no la clase base en sí
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, CloudProviderPlugin) and obj is not CloudProviderPlugin:
                    # Instanciar el plugin y guardarlo en la lista
                    plugins.append(obj())
        except Exception as e:
            # Si un plugin falla al cargarse, el sistema no se detiene, garantizando alta tolerancia a fallos
            print(f"[WARNING] Error cargando el plugin '{module_name}': {e}")
            
    return plugins
