import pymongo
import random
from datetime import datetime

# Conexión a MongoDB
client = pymongo.MongoClient('mongodb://172.31.23.83:27017/')
db = client['biteco_db']
resumenes = db['resumen_mensual_costos']  # ← Nombre corregido

# Limpiar colección existente
resumenes.delete_many({})

print(" Poblando resumen_mensual_costos...")

# Configuración
EMPRESAS = list(range(1, 6))
AREAS = list(range(1, 11))
PROYECTOS = list(range(100, 121))
ANIOS = [2024, 2025, 2026]
MONEDAS = ["USD", "COP", "EUR"]

total_resumenes = 0

for anio in ANIOS:
    for mes in range(1, 13):
        if anio == 2026 and mes > 5:
            continue
        
        for empresa in EMPRESAS:
            for area in AREAS:
                for proyecto in PROYECTOS:
                    if random.random() < 0.8:
                        num_consumos = random.randint(5, 50)
                        costo_total = round(random.uniform(100, 5000), 2)
                        
                        resumen = {
                            "id_resumen": f"{empresa}|{area}|{proyecto}|{anio}|{mes}",
                            "id_empresa": empresa,
                            "id_area": area,
                            "id_proyecto": proyecto,
                            "anio": anio,
                            "mes": mes,
                            "moneda": random.choice(MONEDAS),
                            "costo_total": costo_total * num_consumos,
                            "cantidad_registros": num_consumos,
                            "ultima_actualizacion": datetime.now().isoformat()
                        }
                        
                        resumenes.update_one(
                            {"id_resumen": resumen["id_resumen"]},
                            {"$set": resumen},
                            upsert=True
                        )
                        total_resumenes += 1

print(f" Poblado completado: {total_resumenes} resúmenes")

# Crear índice compuesto (ATTRIBUTE PATTERN)
print("🔧 Creando índice compuesto...")
resumenes.create_index([
    ("id_empresa", 1),
    ("id_area", 1),
    ("id_proyecto", 1),
    ("anio", 1),
    ("mes", 1)
])
print("✅ Índice compuesto creado")
