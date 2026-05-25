import pymongo
import random
from datetime import datetime, timedelta

# Conectar a MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['biteco_db']
consumos = db['consumos']
resumenes = db['resumenes']

# Limpiar colecciones existentes
consumos.delete_many({})
resumenes.delete_many({})

print("🚀 Poblando MongoDB con datos realistas...")

# Configuración
EMPRESAS = list(range(1, 6))
PROYECTOS = list(range(100, 121))  # 100-119
SERVICIOS = ["AWS EC2", "AWS S3", "AWS Lambda", "AWS RDS", "AWS CloudFront", "AWS ELB"]
ANIOS = [2024, 2025, 2026]

# Precios base por servicio (USD)
PRECIOS_BASE = {
    "AWS EC2": {"min": 50, "max": 3000},
    "AWS S3": {"min": 10, "max": 800},
    "AWS Lambda": {"min": 5, "max": 300},
    "AWS RDS": {"min": 100, "max": 2000},
    "AWS CloudFront": {"min": 20, "max": 500},
    "AWS ELB": {"min": 30, "max": 400}
}

total_consumos = 0
total_resumenes = 0

# Generar datos
for anio in ANIOS:
    for mes in range(1, 13):
        # Saltar meses futuros
        if anio == 2026 and mes > 5:
            continue
            
        print(f"📅 Procesando {anio}-{mes:02d}...")
        
        for empresa in EMPRESAS:
            for proyecto in PROYECTOS:
                # Decidir si este proyecto tiene actividad este mes (80% probabilidad)
                if random.random() < 0.8:
                    # Generar entre 5 y 50 consumos por proyecto
                    num_consumos = random.randint(5, 50)
                    
                    costo_total_proyecto = 0
                    cantidad_total = 0
                    servicios_dict = {}
                    
                    for _ in range(num_consumos):
                        servicio = random.choice(SERVICIOS)
                        precio_base = PRECIOS_BASE[servicio]
                        costo = round(random.uniform(precio_base["min"], precio_base["max"]), 2)
                        
                        # Guardar consumo individual
                        consumo = {
                            "id_empresa": empresa,
                            "id_proyecto": proyecto,
                            "nombre_servicio": servicio,
                            "costo": costo,
                            "moneda": "USD",
                            "anio": anio,
                            "mes": mes,
                            "fecha": datetime(anio, mes, random.randint(1, 28))
                        }
                        consumos.insert_one(consumo)
                        total_consumos += 1
                        
                        # Acumular para resumen
                        costo_total_proyecto += costo
                        cantidad_total += 1
                        
                        if servicio not in servicios_dict:
                            servicios_dict[servicio] = {"costo": 0, "cantidad": 0}
                        servicios_dict[servicio]["costo"] += costo
                        servicios_dict[servicio]["cantidad"] += 1
                    
                    # Crear o actualizar resumen
                    resumen = {
                        "id_empresa": empresa,
                        "id_proyecto": proyecto,
                        "anio": anio,
                        "mes": mes,
                        "moneda": "USD",
                        "costo_total": costo_total_proyecto,
                        "cantidad": cantidad_total,
                        "servicios": [
                            {"nombre": k, "costo": v["costo"], "cantidad": v["cantidad"]}
                            for k, v in servicios_dict.items()
                        ],
                        "ultima_actualizacion": datetime.now()
                    }
                    
                    # Upsert
                    resumenes.update_one(
                        {
                            "id_empresa": empresa,
                            "id_proyecto": proyecto,
                            "anio": anio,
                            "mes": mes
                        },
                        {"$set": resumen},
                        upsert=True
                    )
                    total_resumenes += 1

print("\n" + "="*50)
print("📊 ESTADÍSTICAS FINALES:")
print(f"   📝 Total consumos: {total_consumos}")
print(f"   📊 Total resúmenes: {total_resumenes}")
print(f"   🏢 Empresas: {len(EMPRESAS)}")
print(f"   📁 Proyectos: {len(PROYECTOS)}")
print(f"   🔧 Servicios: {len(SERVICIOS)}")
print("="*50)

# Mostrar algunos ejemplos
print("\n🔍 Ejemplo de resumen:")
ejemplo = resumenes.find_one()
print(ejemplo)

print("\n✅ Poblado completado!")
