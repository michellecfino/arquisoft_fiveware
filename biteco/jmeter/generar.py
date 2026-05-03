import csv

salida = "biteco/jmeter/data/solicitudes_20000.csv"

filas = []

proyecto_id = 1
for _empresa in range(1, 41):
    for _area in range(1, 6):
        for _proyecto_local in range(1, 16):
            for mes in range(1, 5):
                filas.append([proyecto_id, 2026, mes])
            proyecto_id += 1

total_deseado = 20000
i = 0
while len(filas) < total_deseado:
    filas.append(filas[i % len(filas)])
    i += 1

# Escribir CSV
with open(salida, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id_proyecto", "anio", "mes"])
    writer.writerows(filas)

print(f"CSV generado con {len(filas)} filas")