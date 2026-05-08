# =============================================================================
# main.tf
# Defines the complete AWS infrastructure for the Availability ASR experiment.
#
# Architecture:
#   - 1 VPC with public and private subnets across 2 AZs
#   - 4 EC2 instances (t2.micro, Ubuntu 24.04, 12GB disk) — app servers
#   - 1 RDS PostgreSQL instance (db.t3.micro) in private subnet
#   - Security Groups for ports 80 (HTTP), 8000 (Django), 5432 (Postgres)
#   - Internet Gateway for public EC2 access
#
# Tácticas de Bass implementadas (infraestructura):
#   - Táctica 1 (Heartbeat): Las EC2 alojan el proceso heartbeat.py que
#     verifica la DB periódicamente. El Security Group de RDS controla quién
#     puede acceder, y revocar esas reglas simula la caída de red para pruebas.
#   - Táctica 2 (Timeout): El statement_timeout de 200ms se aplica en Django,
#     pero la infraestructura RDS (db.t3.micro) tiene suficientes recursos para
#     que el tiempo normal sea < 100ms según el ASR.
#   - Táctica 3 (Degradation): En caso de falla detectada, la capa de app
#     retorna graceful_failure sin colapsar la infraestructura.
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# =============================================================================
# DATA SOURCES
# =============================================================================

# Fetch available AZs in the selected region
data "aws_availability_zones" "available" {
  state = "available"
}

# =============================================================================
# VPC & NETWORKING
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway — required for EC2 instances to be reachable from the internet
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnets (one per AZ) — for EC2 application servers
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
    Tier = "public"
  }
}

# Private Subnets (one per AZ) — for RDS PostgreSQL (no direct internet access)
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
    Tier = "private"
  }
}

# Route Table for public subnets — routes internet traffic through the IGW
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

# Associate public subnets with the public route table
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# =============================================================================
# SECURITY GROUPS
# =============================================================================

# -------------------------------------------------------
# EC2 Security Group
# Allows: HTTP (80), Django dev server (8000), SSH (22)
# -------------------------------------------------------
resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for Django application EC2 instances"
  vpc_id      = aws_vpc.main.id

  # HTTP — load balancer or direct access
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Django dev / gunicorn server port
  ingress {
    description = "Django/Gunicorn"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH for operations (restrict CIDR in production)
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # FIXME: restrict to VPN/bastion CIDR in production
  }

  # Allow all outbound traffic
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}

# -------------------------------------------------------
# RDS Security Group
# Allows: PostgreSQL (5432) — ONLY from EC2 security group
#
# NOTA TÁCTICA: El script fail_db.sh revoca esta regla de ingress
# para simular una caída de red y disparar la táctica de Heartbeat
# + Degradation en la aplicación Django.
# -------------------------------------------------------
resource "aws_security_group" "rds_sg" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for RDS PostgreSQL — only EC2 instances can connect"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL — only accessible from EC2 instances
  ingress {
    description     = "PostgreSQL from EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  # No direct outbound needed for RDS
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

# =============================================================================
# EC2 INSTANCES (4 Application Servers)
# Ubuntu 24.04 LTS, t2.micro, 12GB EBS
# =============================================================================

resource "aws_instance" "app_server" {
  count         = var.ec2_instance_count
  ami           = var.ubuntu_ami
  instance_type = var.ec2_instance_type

  # Distribute instances across available public subnets (round-robin)
  subnet_id                   = aws_subnet.public[count.index % length(aws_subnet.public)].id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  key_name                    = var.key_pair_name
  associate_public_ip_address = true

  # 12 GB root volume as specified
  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.ec2_volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  # Bootstrap: install Python 3.12, pip, Django, psycopg2, redis dependencies
  user_data = <<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y python3.12 python3.12-venv python3-pip redis-server libpq-dev build-essential
    
    # Create app directory
    mkdir -p /opt/disponibilidad/src
    
    # Create virtualenv and install dependencies
    python3.12 -m venv /opt/disponibilidad/venv
    /opt/disponibilidad/venv/bin/pip install --upgrade pip
    /opt/disponibilidad/venv/bin/pip install \
      django==5.0.* \
      psycopg2-binary \
      django-redis \
      gunicorn \
      python-decouple
    
    # Start Redis for cache (Heartbeat state storage)
    systemctl enable redis-server
    systemctl start redis-server
    
    echo "Bootstrap complete on instance ${count.index + 1}" >> /var/log/bootstrap.log
  EOF

  tags = {
    Name = "${var.project_name}-app-server-${count.index + 1}"
    Role = "application"
  }
}

# =============================================================================
# RDS POSTGRESQL (Database)
# db.t3.micro, PostgreSQL 16
# =============================================================================

# RDS Subnet Group — places the DB in private subnets for isolation
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${var.project_name}-rds-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-rds-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-postgres"
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = var.rds_instance_class
  allocated_storage      = 20
  max_allocated_storage  = 100          # autoscaling storage up to 100 GB
  storage_type           = "gp2"
  storage_encrypted      = true

  db_name  = var.rds_db_name
  username = var.rds_username
  password = var.rds_password

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  # Multi-AZ for high availability (can be set to false for experiment cost savings)
  multi_az               = false
  publicly_accessible    = false

  # Backup configuration
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Do NOT delete on terraform destroy without snapshot in production
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-final-snapshot"
  deletion_protection       = false # Set to true in production

  tags = {
    Name = "${var.project_name}-postgres"
    Role = "database"
  }
}
