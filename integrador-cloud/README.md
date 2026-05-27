# Integrador Cloud - Microservicio de Simulación de Consumos de Nube

Este microservicio en Python actúa como el **Manejador de Integración Cloud**. Su propósito principal es simular la generación de consumos de diversos proveedores en la nube y transmitirlos en tiempo real a una API de agregación centralizada.

---

## 🏛️ Diseño Arquitectónico y Atributos de Calidad (ASR)

El desarrollo de este componente se rige estrictamente por principios de diseño e ingeniería de software orientados a la mantenibilidad y extensibilidad:

1. **Patrón de Plugins (Plugin Architecture):**
   Para satisfacer el **ASR de Modificabilidad**, el sistema desacopla cada proveedor cloud del flujo principal. Se utiliza un cargador automático dinámico (`plugins/loader.py`) que detecta y carga en tiempo de ejecución cualquier módulo en el directorio `plugins/` que implemente la clase abstracta base.
   
2. **Encapsulamiento (Encapsulate):**
   Toda la lógica interna de simulación de servicios propios de una nube (por ejemplo, AWS con EC2/S3/Lambda o GCP con Compute Engine/BigQuery) se encuentra encapsulada dentro de su plugin correspondiente. El simulador central desconoce por completo las reglas de negocio de cada proveedor.
   
3. **Abstracción de Servicios Comunes (Abstract Common Services):**
   Se define un contrato común a través de la clase abstracta `CloudProviderPlugin` (en `plugins/base.py`) con el método abstracto obligatorio `generate_consumption()`. Esto garantiza que todos los plugins devuelvan un conjunto normalizado de datos, aislando al simulador del formato nativo del proveedor.

---

## 📁 Estructura del Proyecto

```text
integrador-cloud/
│
├── plugins/
│   ├── base.py              # Clase abstracta CloudProviderPlugin (Contrato común)
│   ├── aws_plugin.py        # Simulación de servicios AWS (EC2, S3, Lambda)
│   ├── gcp_plugin.py        # Simulación de servicios GCP (Compute Engine, Cloud Storage, BigQuery)
│   ├── azure_plugin.py      # Simulación de servicios Azure (App Service, Azure SQL, Functions)
│   └── loader.py            # Cargador dinámico automático de plugins (Reflexión)
│
├── simulator/
│   ├── sender.py            # Clase ConsumptionSender (HTTP POST y control de errores)
│   └── simulator.py         # Orquestador del loop principal (ejecución cada 5 segundos)
│
├── .env                     # Variables de entorno (URL de agregación)
├── .gitignore               # Exclusiones de Git para Python y llaves locales
├── requirements.txt         # Dependencias del proyecto (requests, python-dotenv)
└── README.md                # Esta guía
```

---

## ⚙️ Requisitos y Tecnologías

- **Python 3.12**
- **requests**: Para comunicación HTTP POST.
- **python-dotenv**: Para lectura y carga automática del archivo de variables `.env`.

> [!IMPORTANT]
> **Sin Dependencias Pesadas:** Este microservicio no utiliza bases de datos locales, contenedores Docker ni frameworks pesados (como Django o Flask), lo que garantiza máxima ligereza y portabilidad.

---

## 🚀 Guía de Instalación y Ejecución

Sigue estos pasos para poner en marcha el simulador localmente:

### 1. Clonar y crear la rama (Paso previo)
Si aún no estás en la rama correspondiente, créala:
```bash
git checkout -b feature/cloud-integrator-service
```

### 2. Navegar al directorio e instalar dependencias
Ingresa a la carpeta del microservicio e instala las librerías necesarias:
```bash
cd integrador-cloud
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
El archivo `.env` ya viene configurado con el endpoint de ingesta por defecto:
```env
AGGREGATOR_URL=http://44.203.209.23:8002/api/ingest/
```

### 4. Iniciar el simulador
Ejecuta el orquestador principal:
```bash
python simulator/simulator.py
```

De inmediato verás una salida en consola con formato profesional e información detallada de la recolección:
```text
[2026-05-27 10:25:00] [INFO] =====================================================
[2026-05-27 10:25:00] [INFO] Initializing Cloud Integration Simulator...
[2026-05-27 10:25:00] [INFO] =====================================================
[2026-05-27 10:25:00] [INFO] Successfully loaded 3 plugin(s):
[2026-05-27 10:25:00] [INFO]  - AWSPlugin
[2026-05-27 10:25:00] [INFO]  - GCPPlugin
[2026-05-27 10:25:00] [INFO]  - AzurePlugin
[2026-05-27 10:25:00] [INFO] Aggregator URL configured: http://44.203.209.23:8002/api/ingest/
[2026-05-27 10:25:00] [INFO] Simulator started. Running loop (Ctrl+C to terminate)...
[2026-05-27 10:25:00] [INFO] -----------------------------------------------------
[2026-05-27 10:25:00] [INFO] Sending AWS consumption...
[2026-05-27 10:25:01] [INFO] Response: 200 OK
[2026-05-27 10:25:01] [INFO] Sending GCP consumption...
[2026-05-27 10:25:01] [INFO] Response: 200 OK
...
```

---

## 🛠️ Resiliencia y Control de Errores

El módulo `simulator/sender.py` implementa un manejo robusto de contingencias en la transmisión de red:
- **Timeouts:** Peticiones HTTP limitadas a 5 segundos para impedir que el hilo principal se congele si la red experimenta latencia extrema.
- **Conexión Rechazada:** Si la URL de agregación no está accesible, se registra un mensaje claro de error sin interrumpir ni colapsar el ciclo de vida del simulador.
- **Respuestas HTTP Inválidas:** Si la API devuelve códigos de error (ej. `500`, `404`, `400`), se imprime el código y cuerpo para un diagnóstico inmediato.

---

## 🔌 Demostración de Modificabilidad: Cómo agregar un nuevo proveedor cloud en 1 minuto

Para demostrar que el sistema cumple con el ASR de modificabilidad y el principio **Abierto/Cerrado (Open/Closed Principle)**, supongamos que deseamos agregar un nuevo proveedor como **Oracle Cloud (OCI)**.

**Solo requieres realizar un paso puramente aditivo:**

Crea un archivo nuevo llamado `plugins/oci_plugin.py` con el siguiente código:

```python
import random
from plugins.base import CloudProviderPlugin

class OCIPlugin(CloudProviderPlugin):
    def __init__(self):
        self.services = ["Compute Instance", "Object Storage", "Autonomous DB"]

    def generate_consumption(self) -> dict:
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
```

¡Eso es todo! **No necesitas tocar el cargador (`loader.py`), ni el simulador (`simulator.py`), ni modificar configuraciones.** La próxima vez que inicies el simulador, verás en consola:

```text
[INFO] Successfully loaded 4 plugin(s):
 - AWSPlugin
 - GCPPlugin
 - AzurePlugin
 - OCIPlugin
```

Y el simulador transmitirá inmediatamente los consumos de Oracle Cloud.
