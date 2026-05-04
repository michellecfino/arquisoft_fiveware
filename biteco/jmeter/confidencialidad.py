import csv

salida = "biteco/jmeter/data/solicitudes_confidencialidad.csv"

filas = []

# ── 5000 usuarios AUTORIZADOS ──────────────────────────
# Empresa 1 accede a proyectos de empresa 1 (id_empresa=1)
# Los proyectos 1-15 pertenecen a empresa 1 (según el seed)
for i in range(5000):
    proyecto_id = (i % 15) + 1       # proyectos 1-15 → empresa 1
    empresa_usuario = 1               # usuario dice ser de empresa 1 ✓
    filas.append({
        "tipo":          "autorizado",
        "id_proyecto":   proyecto_id,
        "anio":          2026,
        "mes":           (i % 4) + 1,
        "user_id":       f"user-emp1-{i}",
        "empresa_id":    empresa_usuario,  # coincide con la del proyecto
    })

# ── 5000 usuarios NO AUTORIZADOS ──────────────────────
# Empresa 2 intenta acceder a proyectos de empresa 1
for i in range(5000):
    proyecto_id = (i % 15) + 1       # proyectos 1-15 → empresa 1
    empresa_usuario = 2               # usuario dice ser de empresa 2 ✗
    filas.append({
        "tipo":          "no_autorizado",
        "id_proyecto":   proyecto_id,
        "anio":          2026,
        "mes":           (i % 4) + 1,
        "user_id":       f"user-emp2-{i}",
        "empresa_id":    empresa_usuario,  # NO coincide → debe dar 403
    })

# Crear carpeta si no existe
import os
os.makedirs(os.path.dirname(salida), exist_ok=True)

with open(salida, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "tipo", "id_proyecto", "anio", "mes", "user_id", "empresa_id"
    ])
    writer.writeheader()
    writer.writerows(filas)

print(f"CSV generado con {len(filas)} filas")
print(f"  - Autorizados:     5000")
print(f"  - No autorizados:  5000")