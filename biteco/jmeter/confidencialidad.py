import csv
import os

os.makedirs("biteco/jmeter/data", exist_ok=True)

# Proyectos de empresa 1: 1, 41, 81, ... (75 proyectos, salto de 40)
proyectos_empresa1 = [1 + (i * 40) for i in range(75)]

# Proyectos de empresa 2: 2, 42, 82, ... (75 proyectos, salto de 40)
proyectos_empresa2 = [2 + (i * 40) for i in range(75)]

filas_auth = []
filas_no_auth = []

# Autorizados: empresa 1 accede a sus propios proyectos
for i in range(500):
    proyecto_id = proyectos_empresa1[i % len(proyectos_empresa1)]
    filas_auth.append({
        "tipo": "autorizado",
        "id_proyecto": proyecto_id,
        "anio": 2026,
        "mes": (i % 4) + 1,
        "user_id": f"user-emp1-{i}",
        "empresa_id": 1,
    })

# No autorizados: empresa 2 intenta acceder a proyectos de empresa 1
for i in range(500):
    proyecto_id = proyectos_empresa1[i % len(proyectos_empresa1)]
    filas_no_auth.append({
        "tipo": "no_autorizado",
        "id_proyecto": proyecto_id,
        "anio": 2026,
        "mes": (i % 4) + 1,
        "user_id": f"user-emp2-{i}",
        "empresa_id": 2,
    })

header = ["tipo", "id_proyecto", "anio", "mes", "user_id", "empresa_id"]

with open("biteco/jmeter/data/autorizados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(filas_auth)

with open("biteco/jmeter/data/no_autorizados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(filas_no_auth)

print(f"Autorizados: {len(filas_auth)} filas")
print(f"No autorizados: {len(filas_no_auth)} filas")
print(f"Ejemplo autorizado: proyecto {filas_auth[0]['id_proyecto']} empresa {filas_auth[0]['empresa_id']}")
print(f"Ejemplo no autorizado: proyecto {filas_no_auth[0]['id_proyecto']} empresa {filas_no_auth[0]['empresa_id']}")