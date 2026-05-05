# =========================================================
# Infraestructura INTEGRIDAD - BITECO (CORREGIDA)
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
# SECURITY GROUPS
# =========================================================

# Kong público
resource "aws_security_group" "api_sg" {
  name = "${var.project_prefix}-api-sg"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8001
    to_port     = 8001
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

# Servicios internos (reportes)
resource "aws_security_group" "services_sg" {
  name = "${var.project_prefix}-services-sg"

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
  }

  ingress {
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

# Auditoría
resource "aws_security_group" "audit_sg" {
  name = "${var.project_prefix}-audit-sg"

  ingress {
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

# SSH (reportes incluido)
resource "aws_security_group" "ssh_sg" {
  name = "${var.project_prefix}-ssh-sg"

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

# DB auditoría
resource "aws_security_group" "audit_db_sg" {
  name = "${var.project_prefix}-audit-db-sg"

  ingress {
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

# DB reportes
resource "aws_security_group" "reportes_db_sg" {
  name = "${var.project_prefix}-reportes-db-sg"

  ingress {
    from_port       = 5432
    to_port         = 5432
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

# =========================================================
# KONG (PÚBLICO)
# =========================================================

resource "aws_instance" "kong" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

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
# REPORTES (4 INSTANCIAS)
# =========================================================

resource "aws_instance" "reportes" {
  count         = 4
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  associate_public_ip_address = false

  vpc_security_group_ids = [
    aws_security_group.services_sg.id,
    aws_security_group.ssh_sg.id
  ]

  tags = {
    Name = "reportes-${count.index}"
  }
}

# =========================================================
# AUDITORÍA
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
# RDS AUDITORÍA
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
# RDS REPORTES
# =========================================================

resource "aws_db_instance" "reportes_db" {
  identifier = "reportes-db"

  engine            = "postgres"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  username = "postgres"
  password = "postgres123"

  db_name = "reportes"

  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.reportes_db_sg.id]

  skip_final_snapshot = true
}

# =========================================================
# OUTPUTS
# =========================================================

output "kong_ip" {
  value = aws_instance.kong.public_ip
}

output "reportes_db_endpoint" {
  value = aws_db_instance.reportes_db.address
}

output "audit_db_endpoint" {
  value = aws_db_instance.audit_db.address
}