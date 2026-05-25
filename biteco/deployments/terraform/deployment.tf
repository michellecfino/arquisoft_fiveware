# =========================================================
# Terraform para Agregador de Costos con MongoDB
# =========================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider
provider "aws" {
  region = "us-east-1"
}

# Variables
variable "key_name" {
  description = "Nombre de la key pair de AWS"
  type        = string
  default     = "agregador-key"  # Cambia por tu key pair existente
}

variable "instance_type" {
  description = "Tipo de instancia EC2"
  type        = string
  default     = "t2.micro"
}

# =========================================================
# Data Sources
# =========================================================

# Obtener AMI de Ubuntu 24.04
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# Obtener VPC por defecto
data "aws_vpc" "default" {
  default = true
}

# Obtener subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# =========================================================
# Security Groups
# =========================================================

resource "aws_security_group" "agregador_sg" {
  name        = "agregador-costos-sg"
  description = "Security group for Agregador de Costos"
  vpc_id      = data.aws_vpc.default.id

  # SSH
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Django App
  ingress {
    description = "Django app"
    from_port   = 8002
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # MongoDB (opcional, solo si quieres acceso externo)
  ingress {
    description = "MongoDB"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Salida todo
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "agregador-costos-sg"
  }
}

# =========================================================
# EC2 Instance
# =========================================================

resource "aws_instance" "agregador" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.agregador_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    echo "=== INSTALANDO AGREGADOR DE COSTOS ==="
    
    # Actualizar sistema
    apt-get update -y
    
    # Instalar MongoDB
    echo "Instalando MongoDB..."
    apt-get install -y gnupg curl
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
       gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update -y
    apt-get install -y mongodb-org
    systemctl start mongod
    systemctl enable mongod
    
    # Instalar Python y dependencias
    echo "Instalando Python..."
    apt-get install -y python3-pip git
    
    # Crear directorio de la app
    mkdir -p /opt/agregador
    cd /opt/agregador
    
    # Instalar Django y librerías
    pip3 install django djongo pymongo djangorestframework
    
    # Crear proyecto Django
    django-admin startproject agregador_costos .
    
    # Configurar settings para MongoDB
    cat > agregador_costos/settings.py << 'SETTINGS'
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    SECRET_KEY = 'django-insecure-key-2026'
    DEBUG = True
    ALLOWED_HOSTS = ['*']
    
    DATABASES = {
        'default': {
            'ENGINE': 'djongo',
            'NAME': 'biteco_agregador',
            'ENFORCE_SCHEMA': False,
            'CLIENT': {
                'host': 'mongodb://localhost:27017',
            }
        }
    }
    
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'agregacion',
    ]
    
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    
    ROOT_URLCONF = 'agregador_costos.urls'
    WSGI_APPLICATION = 'agregador_costos.wsgi.application'
    LANGUAGE_CODE = 'es-co'
    TIME_ZONE = 'UTC'
    USE_I18N = True
    USE_TZ = True
    STATIC_URL = 'static/'
    DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
    SETTINGS
    
    # Crear app de agregacion
    python3 manage.py startapp agregacion
    
    # Crear modelos
    cat > agregacion/models.py << 'MODELS'
    from django.db import models
    
    class Consumo(models.Model):
        id_empresa = models.IntegerField()
        id_area = models.IntegerField()
        id_proyecto = models.IntegerField()
        nombre_servicio = models.CharField(max_length=100)
        costo = models.DecimalField(max_digits=14, decimal_places=4)
        moneda = models.CharField(max_length=3)
        anio = models.IntegerField()
        mes = models.IntegerField()
        fecha_consumo = models.DateTimeField(auto_now_add=True)
        
        class Meta:
            indexes = [
                models.Index(fields=['id_proyecto', 'anio', 'mes']),
            ]
    
    class ResumenMensual(models.Model):
        id_empresa = models.IntegerField()
        id_area = models.IntegerField()
        id_proyecto = models.IntegerField()
        anio = models.IntegerField()
        mes = models.IntegerField()
        moneda = models.CharField(max_length=3)
        costo_total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
        cantidad_registros = models.IntegerField(default=0)
        
        class Meta:
            unique_together = [['id_empresa', 'id_area', 'id_proyecto', 'anio', 'mes']]
            indexes = [
                models.Index(fields=['id_proyecto', 'anio', 'mes']),
            ]
    MODELS
    
    # Crear vistas
    cat > agregacion/views.py << 'VIEWS'
    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    from .models import Consumo, ResumenMensual
    
    @api_view(['POST'])
    def ingest(request):
        data = request.data
        Consumo.objects.create(
            id_empresa=data['id_empresa'],
            id_area=data['id_area'],
            id_proyecto=data['id_proyecto'],
            nombre_servicio=data['nombre_servicio'],
            costo=data['costo'],
            moneda=data['moneda'],
            anio=data['anio'],
            mes=data['mes']
        )
        
        resumen, _ = ResumenMensual.objects.get_or_create(
            id_empresa=data['id_empresa'],
            id_area=data['id_area'],
            id_proyecto=data['id_proyecto'],
            anio=data['anio'],
            mes=data['mes'],
            defaults={'moneda': data['moneda']}
        )
        
        resumen.costo_total += data['costo']
        resumen.cantidad_registros += 1
        resumen.save()
        
        return Response({'ok': True})
    
    @api_view(['GET'])
    def resumenes(request):
        query = {}
        if request.GET.get('proyecto'):
            query['id_proyecto'] = int(request.GET.get('proyecto'))
        if request.GET.get('anio'):
            query['anio'] = int(request.GET.get('anio'))
        
        data = list(ResumenMensual.objects.filter(**query).values())
        return Response({'data': data})
    
    @api_view(['GET'])
    def health(request):
        return Response({'status': 'ok', 'mongodb': 'connected'})
    VIEWS
    
    # Crear URLs
    cat > agregacion/urls.py << 'URLS'
    from django.urls import path
    from . import views
    
    urlpatterns = [
        path('ingest/', views.ingest),
        path('resumenes/', views.resumenes),
        path('health/', views.health),
    ]
    URLS
    
    # Actualizar URLs principales
    cat > agregador_costos/urls.py << 'MAIN'
    from django.urls import path, include
    
    urlpatterns = [
        path('api/', include('agregacion.urls')),
    ]
    MAIN
    
    # Ejecutar migraciones
    python3 manage.py makemigrations
    python3 manage.py migrate
    
    # Crear servicio systemd
    cat > /etc/systemd/system/agregador.service << 'SERVICE'
    [Unit]
    Description=Agregador de Costos
    After=network.target mongod.service
    
    [Service]
    User=root
    WorkingDirectory=/opt/agregador
    ExecStart=/usr/local/bin/python3 /opt/agregador/manage.py runserver 0.0.0.0:8002
    Restart=always
    
    [Install]
    WantedBy=multi-user.target
    SERVICE
    
    systemctl daemon-reload
    systemctl enable agregador
    systemctl start agregador
    
    echo "=== INSTALACION COMPLETADA ==="
    echo "IP: $(curl -s ifconfig.me)"
  EOF

  tags = {
    Name = "agregador-costos"
  }
}

# =========================================================
# Outputs
# =========================================================

output "public_ip" {
  description = "IP pública del Agregador de Costos"
  value       = aws_instance.agregador.public_ip
}

output "service_url" {
  description = "URL del servicio"
  value       = "http://${aws_instance.agregador.public_ip}:8002"
}

output "health_check" {
  description = "Endpoint de health check"
  value       = "http://${aws_instance.agregador.public_ip}:8002/api/health/"
}

output "ingest_endpoint" {
  description = "Endpoint para enviar datos"
  value       = "http://${aws_instance.agregador.public_ip}:8002/api/ingest/"
}

output "ssh_command" {
  description = "Comando para conectarse por SSH"
  value       = "ssh -i ${var.key_name}.pem ubuntu@${aws_instance.agregador.public_ip}"
}