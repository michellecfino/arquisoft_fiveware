# Experimento de Disponibilidad — ASR Report Failure

Repositorio completo para el experimento de disponibilidad basado en el **Attribute Scenario Response (ASR)**:

> *"Como usuario empresarial, cuando ocurra una falla en la obtención de datos de reportes, el sistema debe detectar la falla y responder con un mensaje de reintento en un tiempo total máximo de **400ms** (100ms proceso normal + 300ms adicionales por falla)."*

---

## Tácticas de Disponibilidad (Bass et al.)

| # | Táctica | Archivo(s) | Descripción |
|---|---------|-----------|-------------|
| 1 | **Heartbeat** | `src/heartbeat.py`, `src/apps.py`, `src/settings.py` | Hilo daemon que sondea la DB cada 1s y persiste `db_available` en Redis |
| 2 | **Timeout** | `src/settings.py` → `OPTIONS`, `src/services.py` | `statement_timeout=200ms` en PostgreSQL; excepción capturada en services |
| 3 | **Degradation** | `src/views.py` | Retorna `graceful_failure` JSON sin colapsar si Heartbeat=False o Timeout |

### Flujo de decisión en `views.py`

```
GET /api/reports/<id>/
        │
        ▼
cache.get('db_available')   ← Táctica 1: Heartbeat
        │
   False/None ──────────────────────────► graceful_failure  ← Táctica 3
        │ True
        ▼
get_project_report()        ← Táctica 2: Timeout 200ms en DB
        │
    OK ─┤─── ServiceUnavailableError ──► graceful_failure  ← Táctica 3
        │
        ▼
  200 + data
```

---

## Estructura del Repositorio

```
disponibilidad/
├── terraform/
│   ├── main.tf          # VPC, 4 EC2, RDS PostgreSQL, Security Groups
│   ├── variables.tf     # Variables de región, instancias, credenciales
│   └── outputs.tf       # IPs de EC2, endpoint RDS, IDs de SG
├── src/
│   ├── settings.py      # Django config + Timeout (statement_timeout=200ms) + Cache Redis
│   ├── heartbeat.py     # Táctica 1: Heartbeat — hilo daemon de verificación de DB
│   ├── services.py      # Táctica 2: Timeout — consulta SQL con manejo de excepciones
│   ├── views.py         # Táctica 3: Degradation — endpoint con graceful_failure
│   ├── urls.py          # Rutas: /api/reports/<id>/ y /health/
│   ├── apps.py          # AppConfig: inicia HeartbeatService en ready()
│   └── wsgi.py          # Punto de entrada WSGI para Gunicorn
├── scripts/
│   └── fail_db.sh       # Revoca/restaura reglas SG de RDS para simular caída
├── tests/
│   └── availability_test.jmx  # Plan JMeter: carga normal + falla + health check
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Infraestructura AWS (Terraform)

| Recurso | Tipo | Configuración |
|---------|------|---------------|
| VPC | `aws_vpc` | `10.0.0.0/16`, DNS habilitado |
| Subnets públicas | `aws_subnet` | 2 AZs, EC2 |
| Subnets privadas | `aws_subnet` | 2 AZs, RDS |
| EC2 × 4 | `t2.micro` | Ubuntu 24.04, 12GB gp3, Redis local |
| RDS PostgreSQL | `db.t3.micro` | PostgreSQL 16.3, cifrado, subnet privada |
| SG EC2 | `aws_security_group` | Ingress: 80, 8000, 22 |
| SG RDS | `aws_security_group` | Ingress: 5432 solo desde SG de EC2 |

---

## Inicio Rápido

### 1. Infraestructura

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars  # completar credenciales
terraform init
terraform plan
terraform apply

# Guardar outputs para los scripts
export RDS_SG_ID=$(terraform output -raw rds_security_group_id)
export EC2_SG_ID=$(terraform output -raw ec2_security_group_id)
export RDS_HOST=$(terraform output -raw rds_endpoint | cut -d: -f1)
```

### 2. Aplicación Django

```bash
cp .env.example .env
# Editar .env con los valores del output de Terraform

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

### 3. Verificar las tácticas

```bash
# Verificar respuesta normal (< 100ms, status: success)
curl http://localhost:8000/api/reports/1/

# Verificar heartbeat
curl http://localhost:8000/health/

# Simular caída de red → activa Heartbeat + Degradation
./scripts/fail_db.sh revoke

# Verificar respuesta degradada (< 400ms, status: graceful_failure)
curl http://localhost:8000/api/reports/1/

# Restaurar acceso
./scripts/fail_db.sh restore
```

### 4. Pruebas de carga (JMeter)

**Plan contra el ALB (degradación HTML, puerto 80)**

Tras `terraform apply`, usa el output `alb_dns_name` (solo el hostname, sin `http://`). Desde la raíz del proyecto:

```bash
jmeter -n -t test_plan_aws.jmx -l results/aws_alb.jtl -JALB_DNS=disponibilidad-asr-alb-1234567890.us-east-1.elb.amazonaws.com
```

El puerto por defecto es **80** (listener HTTP del ALB). Para fijarlo explícitamente:

```bash
jmeter -n -t test_plan_aws.jmx -l results/aws_alb.jtl -JALB_DNS=<DNS_DEL_ALB> -JALB_PORT=80
```

**Plan legacy (instancia directa)**

```bash
jmeter -n -t tests/availability_test.jmx \
       -l results/results.jtl \
       -e -o results/html_report/ \
       -JDJANGOHOST=<EC2_IP> \
       -JDJANGOPORT=8000
```

---

## Respuestas JSON

**Happy path** (`status: success`):
```json
{
  "status": "success",
  "project_id": 1,
  "found": true,
  "data": { "project_name": "...", "completion_percentage": 75.0 },
  "response_time_ms": 45.2
}
```

**Falla detectada** (`status: graceful_failure`):
```json
{
  "status": "graceful_failure",
  "message": "No pudimos obtener tus datos, por favor reintenta",
  "project_id": 1,
  "data": null,
  "failure_reason": "heartbeat",
  "response_time_ms": 12.5
}
```

---

## Presupuesto de Tiempo (ASR)

```
Ruta normal:   [Request] ──(45ms)──► [DB Query] ──(45ms)──► [Response]  ✓ < 100ms
Ruta de falla: [Request] ──(5ms)───► [Heartbeat cache miss] ──(7ms)───► [graceful_failure] ✓ < 400ms
Ruta timeout:  [Request] ──(200ms)──► [DB Timeout] ──(10ms)──► [graceful_failure] ✓ < 400ms
```
