# =========================================================
# Infraestructura INTEGRIDAD - BITECO
# Arquitectura Segura Final
# =========================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
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
  default = "t3.micro"
}

provider "aws" {
  region = var.region
}

# =========================================================
# VPC
# =========================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_prefix}-vpc"
  }
}

# =========================================================
# INTERNET GATEWAY
# =========================================================

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

# =========================================================
# SUBNETS
# =========================================================

# PUBLICA -> KONG

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet"
  }
}

# PRIVADA -> REPORTES + AUDIT

resource "aws_subnet" "private_app_subnet" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.region}a"

  tags = {
    Name = "private-app-subnet"
  }
}

# PRIVADAS -> DATABASES

resource "aws_subnet" "private_db_subnet_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.region}a"

  tags = {
    Name = "private-db-subnet-1"
  }
}

resource "aws_subnet" "private_db_subnet_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "${var.region}b"

  tags = {
    Name = "private-db-subnet-2"
  }
}

# =========================================================
# ROUTE TABLE PUBLICA
# =========================================================

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route" "internet_route" {
  route_table_id         = aws_route_table.public_rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# =========================================================
# UBUNTU AMI
# =========================================================

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# =========================================================
# SSH KEY
# =========================================================
# Ejecutar localmente:
#
# ssh-keygen -t rsa -b 4096 -f biteco-key
#
# Esto genera:
# - biteco-key
# - biteco-key.pub
# =========================================================

resource "aws_key_pair" "main" {
  key_name   = "biteco-key"
  public_key = file("biteco-key.pub")
}

# =========================================================
# PASSWORDS SEGURAS
# =========================================================

resource "random_password" "audit_db_password" {
  length  = 20
  special = true
}

resource "random_password" "reportes_db_password" {
  length  = 20
  special = true
}

# =========================================================
# SECURITY GROUPS
# =========================================================

# =========================================================
# KONG PUBLICO
# =========================================================

resource "aws_security_group" "api_sg" {
  name   = "${var.project_prefix}-api-sg"
  vpc_id = aws_vpc.main.id

  # API PUBLICA
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ADMIN API SOLO INTERNA
  ingress {
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # SALIDA INTERNET -> Cognito
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "api-sg"
  }
}

# =========================================================
# SSH
# =========================================================

resource "aws_security_group" "ssh_sg" {
  name   = "${var.project_prefix}-ssh-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"

    # SSH desde cualquier IP
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ssh-sg"
  }
}

# =========================================================
# REPORTES
# =========================================================

resource "aws_security_group" "services_sg" {
  name   = "${var.project_prefix}-services-sg"
  vpc_id = aws_vpc.main.id

  # SOLO KONG
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
  }

  # Comunicación interna reportes
  ingress {
    from_port = 8000
    to_port   = 8000
    protocol  = "tcp"
    self      = true
  }

  # HACIA AUDIT
  egress {
    from_port       = 8002
    to_port         = 8002
    protocol        = "tcp"
    security_groups = [aws_security_group.audit_sg.id]
  }

  # HACIA DB REPORTES
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.reportes_db_sg.id]
  }

  tags = {
    Name = "services-sg"
  }
}

# =========================================================
# AUDITORIA
# =========================================================

resource "aws_security_group" "audit_sg" {
  name   = "${var.project_prefix}-audit-sg"
  vpc_id = aws_vpc.main.id

  # LOGS DESDE REPORTES
  ingress {
    from_port       = 8002
    to_port         = 8002
    protocol        = "tcp"
    security_groups = [aws_security_group.services_sg.id]
  }

  # CONSULTAS DESDE KONG
  ingress {
    from_port       = 8002
    to_port         = 8002
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
  }

  # HACIA AUDIT DB
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.audit_db_sg.id]
  }

  tags = {
    Name = "audit-sg"
  }
}

# =========================================================
# AUDIT DB SG
# =========================================================

resource "aws_security_group" "audit_db_sg" {
  name   = "${var.project_prefix}-audit-db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.audit_sg.id]
  }

  tags = {
    Name = "audit-db-sg"
  }
}

# =========================================================
# REPORTES DB SG
# =========================================================

resource "aws_security_group" "reportes_db_sg" {
  name   = "${var.project_prefix}-reportes-db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.services_sg.id]
  }

  tags = {
    Name = "reportes-db-sg"
  }
}

# =========================================================
# KONG
# =========================================================

resource "aws_instance" "kong" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  subnet_id = aws_subnet.public_subnet.id

  associate_public_ip_address = true

  key_name = aws_key_pair.main.key_name

  vpc_security_group_ids = [
    aws_security_group.api_sg.id,
    aws_security_group.ssh_sg.id
  ]

  tags = {
    Name = "kong"
  }
}

# =========================================================
# REPORTES (x4)
# =========================================================

resource "aws_instance" "reportes" {
  count = 4

  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  subnet_id = aws_subnet.private_app_subnet.id

  associate_public_ip_address = false

  key_name = aws_key_pair.main.key_name

  vpc_security_group_ids = [
    aws_security_group.services_sg.id,
    aws_security_group.ssh_sg.id
  ]

  tags = {
    Name = "reportes-${count.index + 1}"
  }
}

# =========================================================
# AUDIT SERVER
# =========================================================

resource "aws_instance" "audit" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  subnet_id = aws_subnet.private_app_subnet.id

  associate_public_ip_address = false

  key_name = aws_key_pair.main.key_name

  vpc_security_group_ids = [
    aws_security_group.audit_sg.id,
    aws_security_group.ssh_sg.id
  ]

  tags = {
    Name = "audit-server"
  }
}

# =========================================================
# DB SUBNET GROUP
# =========================================================

resource "aws_db_subnet_group" "db_subnets" {
  name = "${var.project_prefix}-db-subnets"

  subnet_ids = [
    aws_subnet.private_db_subnet_1.id,
    aws_subnet.private_db_subnet_2.id
  ]
}

# =========================================================
# RDS AUDITORIA
# =========================================================

resource "aws_db_instance" "audit_db" {
  identifier = "audit-db"

  engine         = "postgres"
  engine_version = "16"

  instance_class    = "db.t3.micro"
  allocated_storage = 20

  username = "postgres"
  password = random_password.audit_db_password.result

  publicly_accessible = false

  db_subnet_group_name = aws_db_subnet_group.db_subnets.name

  vpc_security_group_ids = [
    aws_security_group.audit_db_sg.id
  ]

  skip_final_snapshot = true

  tags = {
    Name = "audit-db"
  }
}

# =========================================================
# RDS REPORTES
# =========================================================

resource "aws_db_instance" "reportes_db" {
  identifier = "reportes-db"

  engine         = "postgres"
  engine_version = "16"

  instance_class    = "db.t3.micro"
  allocated_storage = 20

  username = "postgres"
  password = random_password.reportes_db_password.result

  db_name = "reportes"

  publicly_accessible = false

  db_subnet_group_name = aws_db_subnet_group.db_subnets.name

  vpc_security_group_ids = [
    aws_security_group.reportes_db_sg.id
  ]

  skip_final_snapshot = true

  tags = {
    Name = "reportes-db"
  }
}

# =========================================================
# OUTPUTS
# =========================================================

output "kong_public_ip" {
  value = aws_instance.kong.public_ip
}

output "reportes_private_ips" {
  value = aws_instance.reportes[*].private_ip
}

output "audit_private_ip" {
  value = aws_instance.audit.private_ip
}

output "reportes_db_endpoint" {
  value = aws_db_instance.reportes_db.address
}

output "audit_db_endpoint" {
  value = aws_db_instance.audit_db.address
}