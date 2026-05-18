# SSH - Configuración Implementada

## ✅ Cambios Realizados

### 1. Terraform Infrastructure (`terraform/main.tf`)

#### Security Groups - Puertos SSH Abiertos
```hcl
# sg_kong_gateway - Ingress port 22 (SSH)
ingress {
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]  # Abierto a Internet
  description = "SSH access"
}

# sg_servidor_reportes - Ingress port 22 (SSH)
ingress {
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]  # Abierto a Internet  
  description = "SSH access"
}
```

#### AWS Key Pair Resource
```hcl
resource "aws_key_pair" "deployer" {
  key_name   = "${var.project_name}-deployer-key"
  public_key = file(var.ssh_public_key_path)

  tags = {
    Name = "${var.project_name}-deployer-key"
  }
}
```

#### EC2 Instances - Key Pair Assignment
```hcl
# Kong Gateway
resource "aws_instance" "kong_gateway" {
  ...
  key_name = aws_key_pair.deployer.key_name  # ← SSH key pair
}

# Django Servers
resource "aws_instance" "django_servers" {
  ...
  key_name = aws_key_pair.deployer.key_name  # ← SSH key pair
}
```

#### Terraform Outputs - SSH Info
```hcl
output "kong_ssh" {
  description = "SSH command for Kong Gateway"
  value       = "ssh -i <your-private-key> ubuntu@${aws_instance.kong_gateway.public_ip}"
}

output "django_ssh_commands" {
  description = "SSH commands for Django servers (requires bastion or port forwarding)"
  value       = [for i, server in aws_instance.django_servers : "ssh -i <your-private-key> ubuntu@${server.private_ip}"]
}
```

### 2. Variables Terraform (`terraform/variables.tf`)

```hcl
variable "ssh_public_key_path" {
  description = "Path to SSH public key file (e.g., ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_password" {
  description = "Password for SSH access (if PasswordAuthentication enabled)"
  type        = string
  sensitive   = true
  default     = "12345678"
}
```

### 3. User Data Scripts

#### install_kong.sh.tpl
```bash
# Habilitar SSH con PasswordAuthentication
echo "Enabling SSH PasswordAuthentication..."
sed -i 's/^#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd
```

#### install_django.sh.tpl
```bash
# Habilitar SSH con PasswordAuthentication
echo "Enabling SSH PasswordAuthentication..."
sed -i 's/^#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd
```

## 🔒 Seguridad

### Arquitectura SSH

```
JMeter (local)
    ↓
[Kong Gateway - Public Subnet - puerto 22 abierto]
    ↓
    └─→ [4x Django Servers - Private Subnets - puerto 22 abierto]
            ↓
            └─→ [RDS PostgreSQL - Private Subnet - NO SSH]
```

### Security Groups

| Recurso | Ingress SSH | Origen | Egress |
|---------|-----------|--------|---------|
| Kong | 0.0.0.0/0 | Internet (JMeter + Admin) | Django 8000 |
| Django | 0.0.0.0/0 | Internet + Kong | RDS 5432 |
| RDS | N/A (Private) | Django SG | N/A |

### IAM Role (Dual Access)

```hcl
# Mantenemos AmazonSSMManagedInstanceCore para SSM
aws_iam_role_policy_attachment "ssm" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Además ahora tenemos SSH:
resource "aws_key_pair" "deployer" {
  key_name   = "${var.project_name}-deployer-key"
  public_key = file(var.ssh_public_key_path)  # Tu clave pública
}
```

## 📋 Checklist Pre-Despliegue

### Preparar Clave SSH

```bash
# 1. Si no tienes clave SSH local, crear:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# 2. Verificar que la clave pública existe:
ls -la ~/.ssh/id_rsa.pub
cat ~/.ssh/id_rsa.pub  # Copiar contenido

# 3. Crear/Actualizar terraform.tfvars:
cat > terraform/terraform.tfvars <<EOF
project_name = "disponibilidad"
aws_region   = "us-east-1"

ssh_public_key_path = "~/.ssh/id_rsa.pub"  # ← Tu clave pública local

rds_password = "YourSecurePassword123!"
EOF

# 4. Verificar que terraform.tfvars es correcto:
grep ssh_public_key terraform/terraform.tfvars
```

### Desplegar

```bash
cd terraform

# Init (primera vez)
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# Obtener IPs
terraform output kong_public_ip
terraform output kong_ssh
```

## 🚀 Conectar Post-Despliegue

### Kong Gateway

```bash
# Obtener IP
KONG_IP=$(cd terraform && terraform output -raw kong_public_ip)

# Conectar
ssh -i ~/.ssh/id_rsa ubuntu@$KONG_IP

# Verificar dentro:
systemctl status kong
curl -s http://localhost:8000/api/reports/1/ | jq .
```

### Django Servers (via Kong Bastion)

```bash
# Obtener IPs
KONG_IP=$(cd terraform && terraform output -raw kong_public_ip)
DJANGO_IPS=$(cd terraform && terraform output -json django_private_ips | jq -r '.[]')

# Conectar a Django 1
DJANGO_1=$(echo $DJANGO_IPS | jq -r '.[0]')
ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_1

# Dentro:
systemctl status django
cd /opt/disponibilidad && source venv/bin/activate
python manage.py shell
```

### RDS PostgreSQL (desde Django)

```bash
# SSH a Django, luego psql
ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@$DJANGO_1

# Dentro de Django:
psql -h disponibilidad-postgres.XXXXX.us-east-1.rds.amazonaws.com \
     -U dbadmin \
     -d disponibilidad_db

postgres=> SELECT COUNT(*) FROM src_project;
postgres=> SELECT COUNT(*) FROM src_report;
```

## 📖 Documentos Relacionados

- [GUIA_DESPLIEGUE_AWS.md](GUIA_DESPLIEGUE_AWS.md) - Guía completa de despliegue
- [SSH_ACCESO_RAPIDO.md](SSH_ACCESO_RAPIDO.md) - Referencia rápida de SSH
- [CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md) - Todos los cambios del proyecto

## ⚠️ Notas Importantes

1. **Clave Privada**: Mantén `~/.ssh/id_rsa` segura y NO la compartas
2. **terraform.tfvars**: Contiene tu clave pública (segura compartir) pero NO la privada
3. **Security Groups**: SSH está abierto a 0.0.0.0/0 - en producción, restringir a IPs conocidas
4. **Bastion Pattern**: Django servers SOLO son accesibles via Kong (private subnet)
5. **Dual Access**: Puedes usar SSH O AWS Systems Manager Session Manager

## 🔧 Troubleshooting

### SSH Connection Refused
```bash
# Esperar a que userdata script termine (5 min)
# Verificar que Kong está en estado "running"
aws ec2 describe-instances --instance-ids i-XXXX --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress]'
```

### Permission Denied
```bash
# Verificar permisos locales
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Verificar que la clave en terraform es la correcta
diff <(cat ~/.ssh/id_rsa.pub) <(cat terraform/terraform.tfvars | grep ssh_public_key)
```

### Bastion SSH Not Working
```bash
# Verificar que Kong acceso SSH funciona primero:
ssh -i ~/.ssh/id_rsa ubuntu@$KONG_IP "echo OK"

# Luego probar con Django vía bastion:
ssh -i ~/.ssh/id_rsa -J ubuntu@$KONG_IP ubuntu@10.0.10.X "echo OK"

# Agregar -v para verbose:
ssh -i ~/.ssh/id_rsa -v -J ubuntu@$KONG_IP ubuntu@10.0.10.X
```
