# =========================================================
# Infraestructura experimento de escalabilidad - BITECO
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
# Variables
# =========================================================

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_prefix" {
  description = "Prefix used for naming AWS resources"
  type        = string
  default     = "biteco"
}

variable "instance_type_app" {
  description = "EC2 instance type for application hosts"
  type        = string
  default     = "t2.micro"
}

variable "instance_type_broker" {
  description = "EC2 instance type for RabbitMQ broker"
  type        = string
  default     = "t2.micro"
}

variable "instance_type_smtp" {
  description = "EC2 instance type for SMTP simulator"
  type        = string
  default     = "t2.micro"
}

# =========================================================
# Provider
# =========================================================

provider "aws" {
  region = var.region
}

# =========================================================
# Locals
# =========================================================

locals {
  project_name = var.project_prefix

  common_tags = {
    Project   = local.project_name
    ManagedBy = "Terraform"
  }
}

# =========================================================
# Data Source - Ubuntu 24.04
# =========================================================

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# =========================================================
# Security Groups
# =========================================================

resource "aws_security_group" "traffic_django" {
  name        = "${var.project_prefix}-traffic-django"
  description = "Allow application traffic on port 8000"

  ingress {
    description = "HTTP access for Django services"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-django"
  })
}

resource "aws_security_group" "traffic_kong" {
  name        = "${var.project_prefix}-traffic-kong"
  description = "Expose Kong proxy and admin ports"

  ingress {
    description = "Kong proxy"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kong admin"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-kong"
  })
}

resource "aws_security_group" "traffic_db" {
  name        = "${var.project_prefix}-traffic-db"
  description = "Allow PostgreSQL access"

  ingress {
    description = "Traffic to PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-db"
  })
}

resource "aws_security_group" "traffic_ssh" {
  name        = "${var.project_prefix}-traffic-ssh"
  description = "Allow SSH access"

  ingress {
    description = "SSH access from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-ssh"
  })
}

resource "aws_security_group" "traffic_rabbit" {
  name        = "${var.project_prefix}-traffic-rabbit"
  description = "Allow RabbitMQ traffic"

  ingress {
    description = "AMQP"
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "RabbitMQ management"
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-rabbit"
  })
}

resource "aws_security_group" "traffic_smtp" {
  name        = "${var.project_prefix}-traffic-smtp"
  description = "Allow SMTP simulator traffic"

  ingress {
    description = "SMTP"
    from_port   = 1025
    to_port     = 1025
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SMTP simulator UI"
    from_port   = 8025
    to_port     = 8025
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-smtp"
  })
}

# =========================================================
# EC2 - Kong
# =========================================================

resource "aws_instance" "kong" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_kong.id,
    aws_security_group.traffic_ssh.id
  ]

  tags = merge(local.common_tags, {
    Name = "kong-instance",
    Role = "kong"
  })
}

# =========================================================
# EC2 - Reportes
# =========================================================

resource "aws_instance" "reportes_instance_1" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_django.id,
    aws_security_group.traffic_ssh.id,
    aws_security_group.traffic_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-1",
    Role = "reportes"
  })
}

resource "aws_instance" "reportes_instance_2" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_django.id,
    aws_security_group.traffic_ssh.id,
    aws_security_group.traffic_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-2",
    Role = "reportes"
  })
}

resource "aws_instance" "reportes_instance_3" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_django.id,
    aws_security_group.traffic_ssh.id,
    aws_security_group.traffic_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-3",
    Role = "reportes"
  })
}

resource "aws_instance" "reportes_instance_4" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_django.id,
    aws_security_group.traffic_ssh.id,
    aws_security_group.traffic_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-4",
    Role = "reportes"
  })
}

# =========================================================
# EC2 - Broker RabbitMQ
# =========================================================

resource "aws_instance" "broker_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_broker
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_rabbit.id,
    aws_security_group.traffic_ssh.id
  ]

  tags = merge(local.common_tags, {
    Name = "broker-instance",
    Role = "rabbitmq"
  })
}

# =========================================================
# EC2 - Worker Email
# =========================================================

resource "aws_instance" "worker_email_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_ssh.id,
    aws_security_group.traffic_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "worker-email-instance",
    Role = "worker-email"
  })
}

# =========================================================
# EC2 - Simulador SMTP
# =========================================================

resource "aws_instance" "smtp_simulator_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_smtp
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.traffic_smtp.id,
    aws_security_group.traffic_ssh.id
  ]

  tags = merge(local.common_tags, {
    Name = "smtp-simulator-instance",
    Role = "smtp-simulator"
  })
}

# =========================================================
# RDS - PostgreSQL
# =========================================================

resource "aws_db_instance" "rds_postgresql" {
  identifier             = "rds-postgresql"
  engine                 = "postgres"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  username               = "postgres"
  password               = "postgres123"
  db_name                = "biteco"
  skip_final_snapshot    = true
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.traffic_db.id]

  tags = merge(local.common_tags, {
    Name = "rds-postgresql",
    Role = "database"
  })
}

# =========================================================
# Outputs
# =========================================================

output "kong_public_ip" {
  description = "Public IP address for Kong"
  value       = aws_instance.kong.public_ip
}

output "reportes_instance_1_public_ip" {
  description = "Public IP address for reportes instance 1"
  value       = aws_instance.reportes_instance_1.public_ip
}

output "reportes_instance_2_public_ip" {
  description = "Public IP address for reportes instance 2"
  value       = aws_instance.reportes_instance_2.public_ip
}

output "reportes_instance_3_public_ip" {
  description = "Public IP address for reportes instance 3"
  value       = aws_instance.reportes_instance_3.public_ip
}

output "reportes_instance_4_public_ip" {
  description = "Public IP address for reportes instance 4"
  value       = aws_instance.reportes_instance_4.public_ip
}

output "broker_instance_public_ip" {
  description = "Public IP address for broker instance"
  value       = aws_instance.broker_instance.public_ip
}

output "worker_email_instance_public_ip" {
  description = "Public IP address for worker email instance"
  value       = aws_instance.worker_email_instance.public_ip
}

output "smtp_simulator_instance_public_ip" {
  description = "Public IP address for SMTP simulator instance"
  value       = aws_instance.smtp_simulator_instance.public_ip
}

output "rds_postgresql_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.rds_postgresql.address
}