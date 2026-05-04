# =========================================================
# Infraestructura CONFIDENCIALIDAD - BITECO
# =========================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region"         { default = "us-east-1" }
variable "project_prefix" { default = "biteco-conf" }
variable "instance_type"  { default = "t2.micro" }

provider "aws" {
  region = var.region
}

# ─── AMI Ubuntu 24.04 ──────────────────────────────────
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# ─── SECURITY GROUPS ───────────────────────────────────

# SG: API Gateway — único punto público, acepta HTTP de Internet
resource "aws_security_group" "api_sg" {
  name        = "${var.project_prefix}-api-sg"
  description = "API Gateway: solo HTTP publico + SSH"

  ingress {
    description = "HTTP desde Internet"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH deploy"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SG: Servidor Reportes — solo acepta trafico desde API Gateway
# TACTICA: Limit Exposure
resource "aws_security_group" "reportes_sg" {
  name        = "${var.project_prefix}-reportes-sg"
  description = "Servidor Reportes: solo desde API Gateway"

  ingress {
    description     = "Solo desde API Gateway"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
  }

  ingress {
    description = "SSH deploy"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SG: BD Operacional — SOLO desde Servidor Reportes, NUNCA desde Internet
# TACTICA: Limit Exposure — subred privada simulada con Security Group
resource "aws_security_group" "bd_operacional_sg" {
  name        = "${var.project_prefix}-bd-operacional-sg"
  description = "BD Operacional: solo desde Servidor Reportes"

  ingress {
    description     = "Postgres solo desde Reportes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.reportes_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ─── EC2: API Gateway (publico) ────────────────────────
resource "aws_instance" "api_gateway" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.api_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx
    systemctl enable nginx
    systemctl start nginx
  EOF

  tags = { Name = "${var.project_prefix}-api-gateway" }
}

# ─── EC2: Servidor Reportes ────────────────────────────
resource "aws_instance" "servidor_reportes" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  associate_public_ip_address = true

  vpc_security_group_ids = [aws_security_group.reportes_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y python3-pip python3-venv git
  EOF

  tags = { Name = "${var.project_prefix}-servidor-reportes" }
}

# ─── RDS: BD Operacional (privada) ─────────────────────
resource "aws_db_instance" "bd_operacional" {
  identifier        = "${var.project_prefix}-bd-operacional"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "biteco"
  username = "postgres"
  password = "postgres123"

  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.bd_operacional_sg.id]
  skip_final_snapshot    = true

  tags = { Name = "${var.project_prefix}-bd-operacional" }
}

# ─── OUTPUTS ───────────────────────────────────────────
output "api_gateway_ip" {
  value       = aws_instance.api_gateway.public_ip
  description = "IP publica del API Gateway - usar en JMeter"
}

output "servidor_reportes_ip" {
  value       = aws_instance.servidor_reportes.public_ip
  description = "IP para SSH al Servidor Reportes"
}

output "bd_operacional_endpoint" {
  value       = aws_db_instance.bd_operacional.address
  description = "Endpoint RDS - va en el .env del Servidor Reportes"
}