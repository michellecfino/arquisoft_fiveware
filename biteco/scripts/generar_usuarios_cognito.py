import boto3
import csv
import os

REGION          = "us-east-1"
USER_POOL_ID    = os.environ["COGNITO_USER_POOL_ID"]
CLIENT_ID       = os.environ["COGNITO_CLIENT_ID"]
PASSWORD        = "Biteco2026!"

cognito = boto3.client("cognito-idp", region_name=REGION)

def crear_usuario(username, grupo):
    try:
        cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            TemporaryPassword=PASSWORD,
            MessageAction="SUPPRESS",
            UserAttributes=[
                {"Name": "email", "Value": f"{username}@biteco.com"},
                {"Name": "email_verified", "Value": "true"},
            ]
        )
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=username,
            Password=PASSWORD,
            Permanent=True
        )
        cognito.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName=grupo
        )
        print(f"  ✓ {username} ({grupo})")
    except cognito.exceptions.UsernameExistsException:
        print(f"  ~ {username} ya existe")

def obtener_token(username):
    resp = cognito.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": PASSWORD
        },
        ClientId=CLIENT_ID
    )
    return resp["AuthenticationResult"]["IdToken"]

os.makedirs("biteco/jmeter/data", exist_ok=True)

# ── Seguridad: 250 financieros + 250 técnicos ──────────────────────────────
print("=== Creando usuarios financieros (seguridad: 250) ===")
for i in range(250):
    crear_usuario(f"financiero-{i:03d}", "financiero")

print("\n=== Creando usuarios técnicos (seguridad: 250) ===")
for i in range(250):
    crear_usuario(f"tecnico-{i:03d}", "tecnico")

# ── Latencia: financieros adicionales hasta 5000 ───────────────────────────
print("\n=== Creando usuarios financieros adicionales (latencia: 251-4999) ===")
for i in range(250, 5000):
    crear_usuario(f"financiero-{i:03d}", "financiero")

# ── Generar CSV seguridad (250 financieros + 250 técnicos) ─────────────────
print("\n=== Generando CSV seguridad ===")

with open("biteco/jmeter/data/financieros.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["username", "grupo", "id_proyecto", "anio", "mes", "token"])
    for i in range(250):
        username = f"financiero-{i:03d}"
        token = obtener_token(username)
        proyecto = (i % 10) + 1
        mes = (i % 4) + 1
        writer.writerow([username, "financiero", proyecto, 2026, mes, token])
        if i % 25 == 0:
            print(f"  Financieros seguridad: {i+1}/250")

with open("biteco/jmeter/data/tecnicos.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["username", "grupo", "id_proyecto", "anio", "mes", "token"])
    for i in range(250):
        username = f"tecnico-{i:03d}"
        token = obtener_token(username)
        proyecto = (i % 10) + 1
        mes = (i % 4) + 1
        writer.writerow([username, "tecnico", proyecto, 2026, mes, token])
        if i % 25 == 0:
            print(f"  Técnicos seguridad: {i+1}/250")

# ── Generar CSV latencia (5000 financieros) ────────────────────────────────
print("\n=== Generando CSV latencia (5000 financieros) ===")

with open("biteco/jmeter/data/financieros_latencia.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["username", "grupo", "id_proyecto", "anio", "mes", "token"])
    for i in range(5000):
        username = f"financiero-{i:03d}"
        token = obtener_token(username)
        proyecto = (i % 10) + 1
        mes = (i % 4) + 1
        writer.writerow([username, "financiero", proyecto, 2026, mes, token])
        if i % 250 == 0:
            print(f"  Financieros latencia: {i+1}/5000")

print("\n✅ CSVs generados:")
print("   biteco/jmeter/data/financieros.csv        (250 - seguridad)")
print("   biteco/jmeter/data/tecnicos.csv            (250 - seguridad)")
print("   biteco/jmeter/data/financieros_latencia.csv (5000 - latencia)")
print("\n⚠️  Los tokens expiran en 1 día.")