# GUÍA DE DESPLIEGUE EN AWS

## 1. PREREQUISITOS

### Herramientas Necesarias
```bash
# Instaladas localmente
- aws cli v2
- terraform >= 1.9.0
- git
- jmeter (para pruebas)
```

### Credenciales AWS
```bash
# Configurar credenciales
aws configure
# O establecer variables de entorno
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"  # o tu región
```

---

## 2. PREPARACIÓN LOCAL

### Clonar/Verificar Estructura
```bash
cd /path/to/disponibilidad
git status

# Estructura esperada:
# .
# ├── src/
# │   ├── models.py (NEW)
# │   ├── heartbeat.py (UPDATED)
# │   ├── services.py (UPDATED)
# │   ├── views.py (UPDATED)
# │   ├── settings.py (UPDATED)
# │   ├── migrations/ (NEW)
# │   │   ├── 0001_initial.py
# │   │   └── __init__.py
# │   └── ...
# ├── terraform/
# │   ├── main.tf (UPDATED)
# │   ├── variables.tf
# │   ├── install_kong.sh.tpl (NEW)
# │   ├── install_django.sh.tpl (NEW)
# │   ├── seed_db.sql
# │   └── ...
# ├── requirements.txt (UPDATED - sin Redis)
# ├── docker-compose.yml
# ├── Dockerfile
# └── CAMBIOS_REALIZADOS.md (NEW)
```

### Verificar Requirements
```bash
# Sin Redis
cat requirements.txt
# Debe contener:
# Django==5.0.6
# psycopg2-binary==2.9.9
# python-decouple==3.8
# gunicorn==22.0.0
```

---

## 3. CONFIGURAR TERRAFORM VARIABLES

### Crear terraform/terraform.tfvars
```hcl
project_name = "disponibilidad"
aws_region   = "us-east-1"

vpc_cidr              = "10.0.0.0/16"
public_subnet_cidrs   = ["10.0.1.0/24"]
private_subnet_cidrs  = [
  "10.0.10.0/24",  # Django 1
  "10.0.11.0/24",  # Django 2
  "10.0.12.0/24",  # Django 3
  "10.0.13.0/24",  # Django 4
]

rds_instance_class = "db.t3.micro"
rds_db_name        = "disponibilidad_db"
rds_username       = "dbadmin"
rds_password       = "YourSecurePassword123!"  # CAMBIAR ESTO

# SSH Key Pair - proporciona tu clave pública
ssh_public_key_path = "/path/to/your/id_rsa.pub"  # CAMBIAR A TU CLAVE

# Contraseña SSH si usas PasswordAuthentication
ssh_password = "YourSSHPassword123!"  # Opcional, solo para PasswordAuthentication

# Variables adicionales (si existen en variables.tf)
# ec2_instance_count = 4  # Ahora fijo en main.tf
```

### Preparar SSH Key Pair
```bash
# Si no tienes clave SSH, genérala:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Verifica que exista la clave pública:
cat ~/.ssh/id_rsa.pub

# Luego en terraform.tfvars:
ssh_public_key_path = "~/.ssh/id_rsa.pub"
```

### Verificar terraform/variables.tf
Si variables.tf aún tiene referencias antiguas:
```bash
# Revisar que sea compatible con main.tf actualizado
```

### Crear seed_db.sql
```sql
-- Inicializar con datos de prueba
INSERT INTO src_project (name, description, status, created_at, updated_at)
VALUES 
  ('Proyecto Demo', 'Proyecto de demostración para experimento ASR', 'active', NOW(), NOW()),
  ('Proyecto Test', 'Proyecto para testing', 'active', NOW(), NOW());

-- Agregar tareas de ejemplo
INSERT INTO src_task (project_id, name, description, completed, created_at, updated_at)
SELECT id, 'Task 1', 'Primera tarea', false, NOW(), NOW() FROM src_project WHERE name = 'Proyecto Demo'
UNION ALL
SELECT id, 'Task 2', 'Segunda tarea', true, NOW(), NOW() FROM src_project WHERE name = 'Proyecto Demo'
UNION ALL
SELECT id, 'Task 3', 'Tercera tarea', false, NOW(), NOW() FROM src_project WHERE name = 'Proyecto Demo';
```

---

## 4. DESPLEGAR INFRAESTRUCTURA

### Inicializar Terraform
```bash
cd terraform/
terraform init

# Salida esperada:
# Terraform has been successfully initialized!
```

### Validar Configuración
```bash
terraform validate

# Salida esperada:
# Success! The configuration is valid.
```

### Plan de Despliegue
```bash
terraform plan -out=tfplan

# Verificar:
# - 1x Kong Gateway EC2 (public subnet)
# - 4x Django Servers EC2 (private subnets)
# - 1x RDS PostgreSQL (private)
# - Security Groups con mínimo privilegio
# - IAM Role para SSM
```

### Aplicar Despliegue
```bash
terraform apply tfplan

# Salida esperada:
# Apply complete! Resources created: XX
#
# Outputs:
# kong_public_ip = "203.0.113.XXX"
# kong_url = "http://203.0.113.XXX:8000"
# django_private_ips = ["10.0.10.X", "10.0.11.X", "10.0.12.X", "10.0.13.X"]
# rds_endpoint = "disponibilidad-postgres.XXXXX.us-east-1.rds.amazonaws.com:5432"
```

---

## 5. POST-DESPLIEGUE

### Esperar a que las Instancias Arranquen
```bash
# Esperar ~5 minutos para:
# - userdata scripts terminen
# - Kong inicie
# - Django services inicien
# - RDS esté lista

# Verificar EC2
aws ec2 describe-instances \
  --filters "Name=tag:project_name,Values=disponibilidad" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PrivateIpAddress,PublicIpAddress]' \
  --output table
```

### Conectar via SSH al Kong Gateway
```bash
# Kong está en subnet pública con acceso SSH directo
KONG_IP=$(terraform output -raw kong_public_ip)

ssh -i ~/.ssh/id_rsa ubuntu@$KONG_IP

# Dentro del Kong:
systemctl status kong
systemctl restart kong
curl -s http://localhost:8000/api/reports/1/ | jq .
```

### Conectar a Django Server (SSH + Port Forwarding)
```bash
# Django está en subnet privada - usar Kong como bastion
KONG_IP=$(terraform output -raw kong_public_ip)
DJANGO_IP="10.0.10.X"  # Tu IP privada

ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_IP

# Dentro del Django:
cd /opt/disponibilidad
source venv/bin/activate
python manage.py shell
>>> from src.models import Project, Report
>>> Project.objects.count()
>>> Report.objects.count()
```

### Alternativa: AWS Systems Manager Session Manager
```bash
# Sin SSH, también puedes usar SSM:
aws ssm start-session --target <kong-instance-id>
aws ssm start-session --target <django-instance-id>
```

### Configurar Kong Upstreams
El Kong debe conocer los IPs privados de los 4 Django servers.

**Opción A: Admin API Manual**
```bash
# Obtener IPs privadas de Django servers
DJANGO_IPS=$(terraform output -raw django_private_ips)

# Conectar a Kong Admin
KONG_IP=$(terraform output -raw kong_public_ip)

# Crear upstream (si no existe)
curl -X POST http://$KONG_IP:8001/upstreams \
  -d "name=django-cluster" \
  -d "algorithm=round_robin"

# Agregar targets
for IP in $DJANGO_IPS; do
  curl -X POST http://$KONG_IP:8001/upstreams/django-cluster/targets \
    -d "target=$IP:8000"
done
```

**Opción B: Script Post-Apply**
```bash
# Crear terraform/post_deploy.sh
#!/bin/bash
set -e

KONG_IP=$(terraform output -raw kong_public_ip)
DJANGO_IPS=$(terraform output -json django_private_ips | jq -r '.[]')

echo "Configuring Kong Upstream..."
curl -X POST http://$KONG_IP:8001/upstreams \
  -d "name=django-cluster" 2>/dev/null || echo "Upstream may already exist"

for IP in $DJANGO_IPS; do
  echo "Adding target: $IP:8000"
  curl -X POST http://$KONG_IP:8001/upstreams/django-cluster/targets \
    -d "target=$IP:8000"
done

echo "Done!"
```

---

## 6. VERIFICACIÓN DE FUNCIONAMIENTO

### Verificar Kong
```bash
KONG_IP=$(terraform output -raw kong_public_ip)

# Health check
curl -I http://$KONG_IP:8000/api/reports/1/

# Salida esperada (si Django está listo):
# HTTP/1.1 200 OK

# Conectar via SSH
ssh -i ~/.ssh/id_rsa ubuntu@$KONG_IP
systemctl status kong
```

### Verificar Django
```bash
# Conectar a Django server vía SSH bastion
KONG_IP=$(terraform output -raw kong_public_ip)
DJANGO_PRIVATE_IP="10.0.10.X"

ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_PRIVATE_IP
systemctl status django
tail -f /var/log/syslog | grep django

# O via SSM:
aws ssm start-session --target <django-instance-id>
systemctl status django
tail -f /var/log/syslog | grep django
```

### Verificar RDS
```bash
# Conectar desde Django server vía SSH bastion
ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_PRIVATE_IP
psql -h disponibilidad-postgres.XXXXX.us-east-1.rds.amazonaws.com \
     -U dbadmin \
     -d disponibilidad_db

postgres=> SELECT * FROM src_project;
postgres=> SELECT COUNT(*) FROM src_report;

# O via SSM:
aws ssm start-session --target <django-instance-id>
psql -h disponibilidad-postgres.XXXXX.us-east-1.rds.amazonaws.com \
     -U dbadmin \
     -d disponibilidad_db
```

---

## 7. EJECUTAR JMETER TESTS

### Obtener Kong URL
```bash
KONG_URL=$(terraform output -raw kong_url)
echo $KONG_URL
# Output: http://203.0.113.XXX:8000
```

### Actualizar JMeter Test
```bash
# Editar test_plan_aws.jmx
# - Cambiar servidor: ${KONG_IP}:8000
# - Cambiar puerto: 8000
# - Cambiar ruta: /api/reports/1/
```

### Ejecutar Test
```bash
jmeter -n -t test_plan_aws.jmx -l results.jtl -e -o results_html/
```

### Interpretar Resultados
```bash
# Ver agregate_report.html
open results_html/index.html

# Métricas a verificar:
# - Response time: < 400ms (ASR requirement)
# - Throughput
# - Errores (deben ser 0)
```

---

## 8. MONITOREO Y LOGGING

### Ver Logs de Kong
```bash
aws ssm start-session --target <kong-instance-id>

# Dentro:
journalctl -u kong -f
```

### Ver Logs de Django
```bash
aws ssm start-session --target <django-instance-id>

# Dentro:
journalctl -u django -f
tail -f /opt/disponibilidad/error.log
```

### Ver Reportes en BD
```bash
# Conexión directa desde local (si permitida)
psql -h <rds-endpoint> -U dbadmin -d disponibilidad_db

SELECT 
  id, project_id, status, response_time_ms, failure_reason, created_at
FROM src_report
ORDER BY created_at DESC
LIMIT 10;
```

---

## 9. ESCENARIOS DE PRUEBA

### Scenario 1: Funcionamiento Normal
1. JMeter → Kong (8000) → Django 1-4 (8000) → RDS (consulta exitosa)
2. **Esperado:** HTTP 200, response_time < 100ms, Report(status='success')

### Scenario 2: Simular Fallo de BD
```bash
# Dentro de Django server (SSM):
# Parar RDS (desde AWS Console) u inyectar latencia

# Heartbeat detectará fallo en 1-3 segundos
# Views retornará graceful_failure en < 50ms
# Report guardará con status='degraded'
```

### Scenario 3: Fallo de 1 Django Server
```bash
# Dentro de Django server (SSM):
systemctl stop django

# Kong continuará balanceando hacia los otros 3
# Sin impacto en throughput (degradación graceful)
```

---

## 10. DESTRUIR INFRAESTRUCTURA (Cleanup)

```bash
cd terraform/

# Plan de destrucción
terraform plan -destroy

# Aplicar
terraform destroy -auto-approve

# Salida esperada:
# Destroy complete! Resources destroyed.
```

---

## TROUBLESHOOTING

### Django Server no inicia
```bash
aws ssm start-session --target <django-instance-id>

# Verificar logs
tail -100 /var/log/syslog
systemctl status django
journalctl -u django -n 50

# Revisar envvars
cat /opt/disponibilidad/.env

# Ejecutar manualmente
source /opt/disponibilidad/venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Kong no balancea a Django
```bash
# Verificar upstreams en Kong
curl http://<kong-ip>:8001/upstreams
curl http://<kong-ip>:8001/upstreams/django-cluster/targets

# Si está vacío, agregar targets manualmente (ver sección 5)
```

### RDS inaccesible desde Django
```bash
# Verificar Security Groups
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=*sg-rds*" \
  --query 'SecurityGroups[].IpPermissions'

# Verificar que Django SG está autorizado
```

### JMeter resultados deficientes
```bash
# Verificar latencia Kong → Django
# desde Kong server (SSM):
curl -w "@curl-format.txt" -o /dev/null -s http://django-1-ip:8000/api/reports/1/

# Si > 50ms, revisar security groups y network ACLs
```

---

## NOTAS IMPORTANTES

⚠️ **Seguridad:**
- Cambiar `rds_password` a un valor fuerte ANTES de desplegar
- No commitear `terraform.tfvars` con credenciales reales
- Usar AWS Secrets Manager para credenciales en producción

⚠️ **Costos:**
- Kong: t2.micro ≈ $0.012/hora
- Django (4x): t2.micro ≈ $0.048/hora
- RDS: db.t3.micro ≈ $0.017/hora
- **Total:** ≈ $3/día en us-east-1

⚠️ **Limpieza:**
- Destruir con `terraform destroy` cuando termine
- Verificar que no haya recursos huérfanos

---

**Última actualización:** 18 Mayo 2026
**Estado:** ✅ LISTO PARA DESPLEGAR
