# =============================================================================
# main.tf — Arquitectura Distribuida Real (Kong Independiente + 4x Django + RDS)
# =============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.47.0"
    }
  }
}

provider "aws" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# -----------------------------------------------------------------------------
# VPC e Infraestructura de Red
# -----------------------------------------------------------------------------

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
    Tier = "private"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# -----------------------------------------------------------------------------
# SECURITY GROUPS (Diseño Acoplado Limpio sin Ciclos)
# -----------------------------------------------------------------------------

resource "aws_security_group" "sg_kong" {
  name        = "${var.project_name}-sg-kong"
  description = "Instancia dedicada para API Gateway Kong"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Kong proxy desde Internet (JMeter)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH de administracion"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida total"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg-kong" }
}

resource "aws_security_group" "sg_django" {
  name        = "${var.project_name}-sg-django"
  description = "Cluster de servidores Django de reportes"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP Trafico desde Internet o Kong"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH Acceso"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida total"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg-django" }
}

resource "aws_security_group" "sg_rds" {
  name        = "${var.project_name}-sg-rds"
  description = "Acceso restringido a PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "PostgreSQL de Internet para Seeding directo"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description     = "PostgreSQL desde el cluster Django"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.sg_django.id]
  }

  egress {
    description = "Salida total"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg-rds" }
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL 14
# -----------------------------------------------------------------------------

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${var.project_name}-rds-subnet-group"
  subnet_ids = aws_subnet.public[*].id

  tags = { Name = "${var.project_name}-rds-subnet-group" }
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-postgres"
  engine                 = "postgres"
  engine_version         = "14"
  instance_class         = var.rds_instance_class
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp2"
  storage_encrypted      = true

  db_name  = var.rds_db_name
  username = var.rds_username
  password = var.rds_password

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.sg_rds.id]
  publicly_accessible    = true
  skip_final_snapshot    = true
  deletion_protection    = false

  tags = {
    Name = "${var.project_name}-postgres"
    Role = "database"
  }
}

# -----------------------------------------------------------------------------
# EC2 — 1x INSTANCIA EXCLUSIVA PARA KONG GATEWAY (USA SCRIPT INDEPENDIENTE)
# -----------------------------------------------------------------------------

resource "aws_instance" "kong_gateway" {
  depends_on                  = [aws_db_instance.postgres]
  ami                         = "ami-0c7217cdde317cfec" # Amazon Linux 2023 Fijo
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.sg_kong.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.ec2_volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(templatefile("${path.module}/install_kong.sh.tpl", {
    kong_config = file("${path.module}/kong.yml")
  }))

  tags = {
    Name = "${var.project_name}-independent-kong"
    Role = "gateway"
  }
}

# -----------------------------------------------------------------------------
# EC2 — CLÚSTER DE 4x SERVIDORES DJANGO (REPORTES)
# -----------------------------------------------------------------------------

resource "aws_instance" "app_server" {
  depends_on                  = [aws_db_instance.postgres]
  count                       = 4
  ami                         = "ami-0c7217cdde317cfec" # Amazon Linux 2023 Fijo
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public[count.index % length(aws_subnet.public)].id
  vpc_security_group_ids      = [aws_security_group.sg_django.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.ec2_volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(templatefile("${path.module}/install_app.sh.tpl", {
    ssh_password = var.ssh_password
    git_repo     = var.app_git_repo
    db_host      = aws_db_instance.postgres.address
    db_port      = tostring(aws_db_instance.postgres.port)
    db_name      = var.rds_db_name
    db_user      = var.rds_username
    db_password  = var.rds_password
    seed_sql     = file("${path.module}/seed_db.sql")
  }))

  tags = {
    Name = "${var.project_name}-django-node-${count.index + 1}"
    Role = "application"
  }
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------

output "kong_public_ip" {
  description = "IP Publica del Gateway Kong independiente"
  value       = aws_instance.kong_gateway.public_ip
}

output "django_private_ips" {
  description = "IPs de los 4 nodos de la aplicacion"
  value       = aws_instance.app_server[*].private_ip
}

output "rds_endpoint" {
  description = "Endpoint de la base de datos"
  value       = aws_db_instance.postgres.endpoint
}
