import csv

salida = "data/solicitudes_12000.csv"

with open(salida, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id_proyecto", "anio", "mes"])

    proyecto_id = 1
    for _empresa in range(1, 41):
        for _area in range(1, 6):
            for _proyecto_local in range(1, 16):
                for mes in range(1, 5):
                    writer.writerow([
                        proyecto_id,
                        2026,
                        mes,
                    ])
                proyecto_id += 1