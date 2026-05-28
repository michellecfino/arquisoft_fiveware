# =========================================================
# Terraform para Agregador de Costos con MongoDB
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

resource "aws_instance" "agregador" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.agregador_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    echo "=== DESPLEGANDO AGREGADOR DE COSTOS ==="
    
    # Instalar MongoDB
    apt-get update -y
    apt-get install -y gnupg curl
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
       gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update -y
    apt-get install -y mongodb-org
    systemctl start mongod
    systemctl enable mongod
    
    # Configurar MongoDB para acceso externo
    sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
    systemctl restart mongod
    
    # Instalar Python
    apt-get install -y python3-pip git
    
    # Clonar repositorio
    cd /opt
    git clone -b latencia2 https://github.com/michellecfino/arquisoft_fiveware.git
    cd arquisoft_fiveware/biteco/agregador_costos
    
    # Instalar dependencias
    pip3 install -r ../requirements.txt
    
    # Crear índice compuesto en MongoDB
    mongosh --eval '
      db = db.getSiblingDB("biteco_db");
      db.createCollection("resumen_mensual_costos");
      db.resumen_mensual_costos.createIndex({
        "id_empresa": 1, "id_area": 1, "id_proyecto": 1, "anio": 1, "mes": 1
      });
    '
    
    # Poblar base de datos
    python3 -c "exec(open('poblar_mongodb_directo.py').read())"
    
    # Iniciar servidor
    nohup python3 manage.py runserver 0.0.0.0:8002 > /tmp/django.log 2>&1 &
    
    echo "=== DESPLIEGUE COMPLETADO ==="
    echo "IP: $(curl -s ifconfig.me)"
  EOF

  tags = { Name = "agregador-costos" }
}

output "public_ip" {
  value = aws_instance.agregador.public_ip
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
