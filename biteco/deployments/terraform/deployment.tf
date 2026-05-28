# =========================================================
# Terraform para Agregador de Costos con MongoDB
# y Servidor de Reportes con PostgreSQL
# =========================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "key_name" {
  description = "Nombre de la key pair de AWS"
  type        = string
  default     = "vockey"
}

variable "instance_type" {
  description = "Tipo de instancia EC2"
  type        = string
  default     = "t2.micro"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ── Security Group Agregador ───────────────────────────
resource "aws_security_group" "agregador_sg" {
  name        = "agregador-costos-sg"
  description = "Security group for Agregador de Costos"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Django API"
    from_port   = 8002
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "MongoDB"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "agregador-costos-sg" }
}

# ── Security Group Servidor de Reportes ───────────────
resource "aws_security_group" "reportes_sg" {
  name        = "biteco-reportes-sg"
  description = "Servidor de Reportes Django"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Django Reportes"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "biteco-reportes-sg" }
}

# ── EC2 Agregador de Costos ────────────────────────────
resource "aws_instance" "agregador" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.agregador_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y gnupg curl git python3-pip
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
       gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update -y
    apt-get install -y mongodb-org
    systemctl start mongod
    systemctl enable mongod
    sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
    systemctl restart mongod
    cd /opt
    git clone -b seguridad https://github.com/michellecfino/arquisoft_fiveware.git
    cd arquisoft_fiveware/biteco/agregador_costos
    pip3 install -r ../requirements.txt --break-system-packages
    mongosh --eval '
      db = db.getSiblingDB("biteco_db");
      db.createCollection("resumen_mensual_costos");
      db.resumen_mensual_costos.createIndex({
        "id_empresa": 1, "id_area": 1, "id_proyecto": 1, "anio": 1, "mes": 1
      });
    '
    python3 -c "exec(open('poblar_mongodb_directo.py').read())"
    nohup python3 manage.py runserver 0.0.0.0:8002 > /tmp/agregador.log 2>&1 &
  EOF

  tags = { Name = "agregador-costos" }
}

# ── EC2 Servidor de Reportes ───────────────────────────
resource "aws_instance" "reportes" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.reportes_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y python3-pip git
    cd /opt
    git clone -b seguridad https://github.com/michellecfino/arquisoft_fiveware.git
    cd arquisoft_fiveware/biteco
    pip3 install -r requirements.txt --break-system-packages
    cd manejador_reportes
    cat > manejador_reportes/settings.py << 'SETTEOF'
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "dev-manejador-reportes"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","reportes"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "manejador_reportes.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "manejador_reportes.wsgi.application"
DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql_psycopg2","NAME":"biteco","USER":"postgres","PASSWORD":"postgres123","HOST":"${aws_db_instance.bd_reportes.address}","PORT":"5432"}}
LANGUAGE_CODE = "es-co"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SETTEOF
    python3 manage.py migrate
    nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/reportes.log 2>&1 &
  EOF

  depends_on = [aws_db_instance.bd_reportes]
  tags = { Name = "servidor-reportes" }
}

# ── Outputs ────────────────────────────────────────────
output "public_ip" {
  value = aws_instance.agregador.public_ip
}

output "reportes_ip" {
  value = aws_instance.reportes.public_ip
}

output "service_url" {
  value = "http://${aws_instance.agregador.public_ip}:8002"
}

output "health_check" {
  value = "http://${aws_instance.agregador.public_ip}:8002/api/health/"
}

output "ingest_endpoint" {
  value = "http://${aws_instance.agregador.public_ip}:8002/api/ingest/"
}

output "ssh_command" {
  value = "ssh -i ${var.key_name}.pem ubuntu@${aws_instance.agregador.public_ip}"
}