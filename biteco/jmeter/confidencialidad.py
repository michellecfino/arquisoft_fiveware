import csv
import os
import jwt  # PyJWT

SECRET = "experimento-biteco-confidencialidad"
os.makedirs("biteco/jmeter/data", exist_ok=True)

proyectos_empresa1 = [1 + (i * 40) for i in range(75)]

filas_auth = []
filas_no_auth = []

for i in range(5000):
    proyecto_id = proyectos_empresa1[i % 75]
    mes = (i % 4) + 1
    user_id = f"user-emp1-{i}"

    token = jwt.encode(
        {"sub": user_id, "empresa_id": 1, "role": "user"},
        SECRET,
        algorithm="HS256"
    )

    filas_auth.append({
        "tipo": "autorizado",
        "id_proyecto": proyecto_id,
        "anio": 2026,
        "mes": mes,
        "user_id": user_id,
        "empresa_id": 1,
        "token": token,
    })

for i in range(5000):
    proyecto_id = proyectos_empresa1[i % 75]
    mes = (i % 4) + 1
    user_id = f"user-emp2-{i}"

    token = jwt.encode(
        {"sub": user_id, "empresa_id": 2, "role": "user"},
        SECRET,
        algorithm="HS256"
    )

    filas_no_auth.append({
        "tipo": "no_autorizado",
        "id_proyecto": proyecto_id,
        "anio": 2026,
        "mes": mes,
        "user_id": user_id,
        "empresa_id": 2,
        "token": token,
    })

header = ["tipo", "id_proyecto", "anio", "mes", "user_id", "empresa_id", "token"]

with open("biteco/jmeter/data/autorizados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(filas_auth)

with open("biteco/jmeter/data/no_autorizados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(filas_no_auth)

print(f"Autorizados:    {len(filas_auth)} filas")
print(f"No autorizados: {len(filas_no_auth)} filas")
print(f"Ejemplo token autorizado:    {filas_auth[0]['token'][:60]}...")
print(f"Ejemplo token no autorizado: {filas_no_auth[0]['token'][:60]}...")