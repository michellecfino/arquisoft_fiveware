import os
import sys
import time
import logging
from dotenv import load_dotenv

# Configuración del path para permitir importaciones modulares robustas
# de forma que se pueda ejecutar tanto desde 'integrador-cloud' como desde la raíz del repo
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# Importamos las dependencias internas tras configurar el PYTHONPATH
from plugins.loader import load_plugins
from sender import ConsumptionSender, logger

def run_simulator():
    """
    Orquestador principal del simulador.
    
    Carga variables de entorno, importa dinámicamente los plugins,
    e inicia un loop infinito que recolecta y transmite los consumos cada 5 segundos.
    """
    logger.info("=====================================================")
    logger.info("Initializing Cloud Integration Simulator...")
    logger.info("=====================================================")

    # Cargar variables de entorno (.env)
    load_dotenv(os.path.join(PARENT_DIR, ".env"))

    # Cargar plugins automáticamente usando el Loader dinámico
    # MODIFICABILIDAD: El cargador escanea la carpeta y retorna las instancias listas
    plugins = load_plugins()
    
    if not plugins:
        logger.error("No active cloud provider plugins were found in 'plugins/' folder. Exiting...")
        sys.exit(1)
        
    logger.info(f"Successfully loaded {len(plugins)} plugin(s):")
    for plugin in plugins:
        logger.info(f" - {plugin.__class__.__name__}")
        
    # Inicializar el servicio de transmisión de datos (Sender)
    sender = ConsumptionSender()
    logger.info(f"Aggregator URL configured: {sender.url}")
    logger.info("Simulator started. Running loop (Ctrl+C to terminate)...")
    logger.info("-----------------------------------------------------")

    try:
        while True:
            for plugin in plugins:
                # Obtener el nombre limpio del proveedor (e.g., AWSPlugin -> AWS)
                provider_name = plugin.__class__.__name__.replace("Plugin", "")
                
                try:
                    # Contrato común y encapsulamiento: Llamamos al método definido en la interfaz
                    consumption_data = plugin.generate_consumption()
                    
                    # Enviar el consumo normalizado a través del remitente HTTP
                    sender.send(provider_name, consumption_data)
                    
                except Exception as e:
                    logger.error(f"Execution error inside '{plugin.__class__.__name__}': {e}")
                    
            # Intervalo de ejecución requerido: 5 segundos
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("\nSimulator terminated by user. Goodbye!")

if __name__ == "__main__":
    run_simulator()
