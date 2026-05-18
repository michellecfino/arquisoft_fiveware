# =============================================================================
# main.tf — Kong Gateway + 4 Django Servers (privado) + RDS PostgreSQL
# =============================================================================
# Kong Gateway: proxy y API Gateway en subnet pública
# 4 Django Servers: subnets privadas (sin acceso directo a Internet)
# RDS: subnet privada (NO públicamente accesible)
# SSM: acceso sin SSH (Systems Manager Session Manager)
# Mínimo Privilegio en Security Groups
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

# ---------- Obtener AMI Ubuntu 24.04 LTS más reciente ----------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# -----------------------------------------------------------------------------
# VPC
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

# SUBNET PÚBLICA (Kong Gateway)
resource "aws_subnet" "public" {
  count                   = 1
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[0]
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-kong"
    Tier = "public"
  }
}

# SUBNETS PRIVADAS (4 Django Servers)
resource "aws_subnet" "private" {
  count             = 4
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
    Tier = "private"
  }
}

# ROUTE TABLE PÚBLICA
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.igw.id
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

# ROUTE TABLE PRIVADA (sin IGW directo)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# =============================================================================
# IAM ROLE PARA SSM (AWS Systems Manager)
# =============================================================================

resource "aws_iam_role" "ssm_role" {
  name = "${var.project_name}-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ssm-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm_profile" {
  name = "${var.project_name}-ssm-profile"
  role = aws_iam_role.ssm_role.name
}

# =============================================================================
# SECURITY GROUPS (Mínimo Privilegio)
# =============================================================================

# SG: Kong Gateway
resource "aws_security_group" "sg_kong_gateway" {
  name        = "${var.project_name}-sg-kong"
  description = "Kong Gateway - proxy and API Gateway"
  vpc_id      = aws_vpc.main.id

  # Ingress: HTTP/8000 desde Internet (JMeter)
  ingress {
    description = "Kong proxy from JMeter"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Ingress: SSH desde Internet
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress: HTTP hacia Django servers (Removido inline para evitar ciclo)

  # Egress: HTTPS outbound
  egress {
    description = "HTTPS outbound"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress: DNS
  egress {
    description = "DNS"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg-kong"
  }
}

# SG: Django Servers (Servidor de Reportes)
resource "aws_security_group" "sg_servidor_reportes" {
  name        = "${var.project_name}-sg-django"
  description = "Django reporting servers - restricted to Kong"
  vpc_id      = aws_vpc.main.id

  # Ingress: HTTP/8000 SOLO desde Kong
  ingress {
    description     = "Django app from Kong"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.sg_kong_gateway.id]
  }
  # Ingress: SSH desde Internet (para administración directa)
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Egress: PostgreSQL hacia RDS (Removido inline para evitar ciclo)

  # Egress: HTTPS outbound
  egress {
    description = "HTTPS outbound"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress: DNS
  egress {
    description = "DNS"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg-django"
  }
}

# SG: RDS Database
resource "aws_security_group" "sg_database" {
  name        = "${var.project_name}-sg-rds"
  description = "RDS PostgreSQL - restricted to Django servers only"
  vpc_id      = aws_vpc.main.id

  # Ingress: PostgreSQL SOLO desde Django (Removido inline para evitar ciclo)

  # Egress: Permitir
  egress {
    description = "Allow outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg-rds"
  }
}

# =============================================================================
# RDS POSTGRESQL (SUBNET PRIVADA - NO PÚBLICO)
# =============================================================================

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
  engine_version         = "14.7"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp3"
  storage_encrypted      = true

  db_name  = var.rds_db_name
  username = var.rds_username
  password = var.rds_password

  db_subnet_group_name            = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids          = [aws_security_group.sg_database.id]
  publicly_accessible             = false
  iam_database_authentication_enabled = true

  multi_az            = false
  skip_final_snapshot = true

  tags = {
    Name = "${var.project_name}-postgres"
    Role = "database"
  }
}

# =============================================================================
# SSH KEY PAIR
# =============================================================================

resource "aws_key_pair" "deployer" {
  key_name   = "${var.project_name}-key"
  public_key = file(var.ssh_public_key_path)

  tags = {
    Name = "${var.project_name}-key"
  }
}

# =============================================================================
# EC2 — KONG GATEWAY (PUBLIC SUBNET)
# =============================================================================

resource "aws_instance" "kong_gateway" {
  depends_on              = [aws_db_instance.postgres]
  ami                     = data.aws_ami.ubuntu.id
  instance_type           = "t2.micro"
  subnet_id               = aws_subnet.public[0].id
  vpc_security_group_ids  = [aws_security_group.sg_kong_gateway.id]
  iam_instance_profile    = aws_iam_instance_profile.ssm_profile.name
  key_name                = aws_key_pair.deployer.key_name
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 16
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(templatefile("${path.module}/install_kong.sh.tpl", {
    django_ips = [for i in aws_instance.django_servers : i.private_ip]
  }))

  tags = {
    Name = "${var.project_name}-kong-gateway"
    Role = "gateway"
  }
}

# =============================================================================
# EC2 — 4 DJANGO SERVERS (PRIVATE SUBNETS)
# =============================================================================

resource "aws_instance" "django_servers" {
  count                  = 4
  depends_on             = [aws_db_instance.postgres]
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.private[count.index].id
  vpc_security_group_ids = [aws_security_group.sg_servidor_reportes.id]
  iam_instance_profile   = aws_iam_instance_profile.ssm_profile.name
  key_name               = aws_key_pair.deployer.key_name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 12
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(templatefile("${path.module}/install_django.sh.tpl", {
    db_host      = aws_db_instance.postgres.address
    db_port      = tostring(aws_db_instance.postgres.port)
    db_name      = var.rds_db_name
    db_user      = var.rds_username
    db_password  = var.rds_password
    seed_sql     = file("${path.module}/seed_db.sql")
  }))

  tags = {
    Name = "${var.project_name}-django-server-${count.index + 1}"
    Role = "application"
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "kong_public_ip" {
  description = "Kong Gateway public IP"
  value       = aws_instance.kong_gateway.public_ip
}

output "kong_url" {
  description = "Kong Gateway endpoint"
  value       = "http://${aws_instance.kong_gateway.public_ip}:8000"
}

output "kong_ssh" {
  description = "SSH command for Kong Gateway"
  value       = "ssh -i <your-private-key> ubuntu@${aws_instance.kong_gateway.public_ip}"
}

output "django_private_ips" {
  description = "Django servers private IPs"
  value       = [for i in aws_instance.django_servers : i.private_ip]
}

output "django_ssh_commands" {
  description = "SSH commands for Django servers (requires bastion or port forwarding)"
  value       = [for i, server in aws_instance.django_servers : "ssh -i <your-private-key> ubuntu@${server.private_ip}"]
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS PostgreSQL address only"
  value       = aws_db_instance.postgres.address
}


# =============================================================================
# REGLAS INDEPENDIENTES PARA ROMPER EL CICLO DE DEPENDENCIAS
# =============================================================================

# 1. Permitir que Kong envíe tráfico a Django en el puerto 8000
resource "aws_security_group_rule" "kong_to_django_egress" {
  type                     = "egress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  security_group_id        = aws_security_group.sg_kong_gateway.id
  source_security_group_id = aws_security_group.sg_servidor_reportes.id
}

# 2. Permitir que Django envíe tráfico a la RDS en el puerto 5432
resource "aws_security_group_rule" "django_to_rds_egress" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.sg_servidor_reportes.id
  source_security_group_id = aws_security_group.sg_database.id
}

# 3. Permitir que la RDS reciba el tráfico de Django en el puerto 5432
resource "aws_security_group_rule" "rds_from_django_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.sg_database.id
  source_security_group_id = aws_security_group.sg_servidor_reportes.id
}