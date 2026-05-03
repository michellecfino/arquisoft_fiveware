# =========================================================
# Infraestructura INTEGRIDAD - BITECO
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

# =========================================================
# VARIABLES
# =========================================================

variable "region" {
  default = "us-east-1"
}

variable "project_prefix" {
  default = "biteco"
}

variable "instance_type" {
  default = "t2.micro"
}

variable "auth0_domain" {}
variable "auth0_audience" {}

provider "aws" {
  region = var.region
}

# =========================================================
# AMI UBUNTU
# =========================================================

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# =========================================================
# SECURITY GROUPS (CORRECTOS)
# =========================================================

# API Gateway (Kong)
resource "aws_security_group" "api_sg" {
  name = "${var.project_prefix}-api-sg"

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
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

# Servicios (Reportes)
resource "aws_security_group" "services_sg" {
  name = "${var.project_prefix}-services-sg"

  # SOLO desde API Gateway
  ingress {
    description     = "From API Gateway"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
  }

  # Comunicación interna
  ingress {
    description = "Internal communication"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Auditoría (Logs)
resource "aws_security_group" "audit_sg" {
  name = "${var.project_prefix}-audit-sg"

  ingress {
    description     = "Only from services"
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.services_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# BD Auditoría
resource "aws_security_group" "audit_db_sg" {
  name = "${var.project_prefix}-audit-db-sg"

  ingress {
    description     = "Only from audit service"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.audit_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SSH (solo pruebas)
resource "aws_security_group" "ssh_sg" {
  name = "${var.project_prefix}-ssh"

  ingress {
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

# =========================================================
# API GATEWAY + AUTH0
# =========================================================

resource "aws_apigatewayv2_api" "api" {
  name          = "biteco-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "auth0" {
  api_id          = aws_apigatewayv2_api.api.id
  authorizer_type = "JWT"

  identity_sources = ["$request.header.Authorization"]

  name = "auth0-authorizer"

  jwt_configuration {
    issuer   = "https://${var.auth0_domain}/"
    audience = [var.auth0_audience]
  }
}

# =========================================================
# EC2 - KONG (ÚNICO PUNTO PÚBLICO)
# =========================================================

resource "aws_instance" "kong" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  associate_public_ip_address = true

  vpc_security_group_ids = [
    aws_security_group.api_sg.id,
    aws_security_group.ssh_sg.id
  ]

  tags = {
    Name = "kong"
  }
}

# =========================================================
# CLUSTER REPORTES (PRIVADO)
# =========================================================

resource "aws_instance" "reportes" {
  count         = 3
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  associate_public_ip_address = false

  vpc_security_group_ids = [
    aws_security_group.services_sg.id
  ]

  tags = {
    Name = "reportes-${count.index}"
  }
}

# =========================================================
# MANEJADOR LOGS (PRIVADO)
# =========================================================

resource "aws_instance" "audit" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  associate_public_ip_address = false

  vpc_security_group_ids = [
    aws_security_group.audit_sg.id,
    aws_security_group.ssh_sg.id
  ]

  tags = {
    Name = "audit-server"
  }
}

# =========================================================
# RDS AUDITORÍA (AISLADA)
# =========================================================

resource "aws_db_instance" "audit_db" {
  identifier = "audit-db"

  engine            = "postgres"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  username = "postgres"
  password = "postgres123"

  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.audit_db_sg.id]

  skip_final_snapshot = true
}

# =========================================================
# OUTPUTS
# =========================================================

output "kong_ip" {
  value = aws_instance.kong.public_ip
}

output "api_gateway_url" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "audit_db_endpoint" {
  value = aws_db_instance.audit_db.address
}