# SSH - Acceso Rápido

## Preparación Inicial

```bash
# 1. Generar clave SSH (si no tienes)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# 2. Configurar en terraform.tfvars
ssh_public_key_path = "~/.ssh/id_rsa.pub"

# 3. Desplegar infraestructura
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## Conectar a Kong Gateway

Kong está en una **subnet pública** con acceso SSH directo desde Internet.

```bash
# Obtener IP pública de Kong
KONG_IP=$(terraform output -raw kong_public_ip)

# Conectar
ssh -i ~/.ssh/id_rsa ubuntu@$KONG_IP

# Ejemplos dentro de Kong:
systemctl status kong
curl -s http://localhost:8000/api/reports/1/ | jq .
curl -s http://localhost:8001/  # Admin API de Kong
```

## Conectar a Django Servers

Django servers están en **subnets privadas** - necesitan bastion (Kong).

```bash
# Obtener IPs
KONG_IP=$(terraform output -raw kong_public_ip)
DJANGO_IPS=$(terraform output -json django_private_ips | jq -r '.[]')

# Conectar a Django 1 vía Kong
DJANGO_IP="${DJANGO_IPS[0]}"
ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_IP

# Ejemplos dentro de Django:
systemctl status django
tail -f /var/log/syslog | grep django
cd /opt/disponibilidad && source venv/bin/activate
python manage.py dbshell
```

## Conectar a RDS PostgreSQL

RDS está en una **subnet privada** - accesible SOLO desde Django servers.

```bash
# Opción A: SSH a Django, luego psql
ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_IP

# Dentro de Django:
DJANGO_IP="10.0.10.X"
RDS_HOST="disponibilidad-postgres.XXXXX.us-east-1.rds.amazonaws.com"
psql -h $RDS_HOST -U dbadmin -d disponibilidad_db

# Consultas útiles:
postgres=> SELECT COUNT(*) FROM src_project;
postgres=> SELECT COUNT(*) FROM src_report;
postgres=> SELECT * FROM src_report ORDER BY created_at DESC LIMIT 5;
```

## Agregar Nuevas Claves SSH

Si quieres agregar más clave pública (para otros usuarios):

```bash
# 1. En tu máquina local, generar otra clave
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_otro_usuario

# 2. Conectar via SSH existente a Kong
ssh -i ~/.ssh/id_rsa ubuntu@$KONG_IP

# 3. Dentro de Kong, agregar la nueva clave a authorized_keys
echo "ssh-rsa AAAA... otro_usuario@laptop" >> ~/.ssh/authorized_keys

# 4. Ahora ese usuario puede conectar directamente
ssh -i ~/.ssh/id_rsa_otro_usuario ubuntu@$KONG_IP
```

## Troubleshooting

### "Permission denied (publickey)"
```bash
# Verificar permisos de clave local
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Verificar que la clave está en terraform.tfvars correctamente
cat ~/.ssh/id_rsa.pub  # Copiar output
# Asegurarse que en terraform.tfvars está bien:
ssh_public_key_path = "~/.ssh/id_rsa.pub"
```

### "Could not resolve hostname"
```bash
# Verificar que Kong está corriendo
aws ec2 describe-instances --query 'Reservations[].Instances[?Tags[?Key==`Name`]|[0].Value==`disponibilidad-asr-kong-gateway`].PublicIpAddress' --output text

# Si IP está vacía, esperar más tiempo (userdata script)
```

### SSH Timeout
```bash
# Verificar que Security Group permite puerto 22:
aws ec2 describe-security-groups --query 'SecurityGroups[?GroupName==`sg_kong_gateway`].IpPermissions'

# Debe mostrar:
# - FromPort: 22
# - ToPort: 22
# - IpRange: 0.0.0.0/0
```

## SSH Config (Opcional)

Para simplificar comandos, crear `~/.ssh/config`:

```
Host kong
    HostName <KONG_IP>
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no

Host django1 
    HostName 10.0.10.X
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    ProxyJump kong
    StrictHostKeyChecking no

Host django2
    HostName 10.0.11.X
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    ProxyJump kong
    StrictHostKeyChecking no

Host django3
    HostName 10.0.12.X
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    ProxyJump kong
    StrictHostKeyChecking no

Host django4
    HostName 10.0.13.X
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    ProxyJump kong
    StrictHostKeyChecking no
```

Luego puedes usar:
```bash
# Conectar a Kong
ssh kong

# Conectar a Django 1 (automáticamente vía Kong)
ssh django1

# Ver logs en Django 3
ssh django3 "tail -f /var/log/syslog | grep django"
```

## Alternativa: AWS Systems Manager Session Manager

Si prefieres no usar SSH, AWS SSM funciona como alternativa:

```bash
# Conectar a Kong
aws ssm start-session --target i-0123456789abcdef0

# Sin necesidad de gestionar claves SSH
```

Pero SSH es más flexible y recomendado para desarrollo.
