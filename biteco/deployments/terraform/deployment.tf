terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project_prefix" {
  type    = string
  default = "biteco"
}

variable "instance_type_app" {
  type    = string
  default = "t2.micro"
}

variable "instance_type_broker" {
  type    = string
  default = "t2.nano"
}

variable "instance_type_smtp" {
  type    = string
  default = "t2.nano"
}

variable "key_name" {
  type = string
}

provider "aws" {
  region = var.region
}

locals {
  common_tags = {
    Project = var.project_prefix
  }
}

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

resource "aws_security_group" "trafico_ssh" {
  name        = "${var.project_prefix}-trafico-ssh"
  description = "Permite acceso SSH"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida general para administracion"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "trafico-ssh"
  })
}

resource "aws_security_group" "trafico_kong" {
  name        = "${var.project_prefix}-trafico-kong"
  description = "Permite trafico Kong"

  ingress {
    description = "Kong Proxy"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kong Admin"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "trafico-kong"
  })
}

resource "aws_security_group" "trafico_django" {
  name        = "${var.project_prefix}-trafico-django"
  description = "Permite trafico a instancias Django"

  ingress {
    description = "Django app"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "trafico-django"
  })
}

resource "aws_security_group" "trafico_db" {
  name        = "${var.project_prefix}-trafico-db"
  description = "Permite trafico PostgreSQL"

  ingress {
    description = "PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "trafico-db"
  })
}

resource "aws_security_group" "trafico_rabbit" {
  name        = "${var.project_prefix}-trafico-rabbit"
  description = "Permite trafico RabbitMQ"

  ingress {
    description = "AMQP"
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "RabbitMQ Management"
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "trafico-rabbit"
  })
}

resource "aws_security_group" "trafico_smtp" {
  name        = "${var.project_prefix}-trafico-smtp"
  description = "Permite trafico SMTP de pruebas"

  ingress {
    description = "SMTP test server"
    from_port   = 1025
    to_port     = 1025
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SMTP test UI"
    from_port   = 8025
    to_port     = 8025
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "trafico-smtp"
  })
}

resource "aws_instance" "kong_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_kong.id,
    aws_security_group.trafico_ssh.id
  ]

  tags = merge(local.common_tags, {
    Name = "kong-instance"
    Role = "kong"
  })
}

resource "aws_instance" "reportes_instance_1" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_django.id,
    aws_security_group.trafico_ssh.id,
    aws_security_group.trafico_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-1"
    Role = "reportes"
  })
}

resource "aws_instance" "reportes_instance_2" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_django.id,
    aws_security_group.trafico_ssh.id,
    aws_security_group.trafico_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-2"
    Role = "reportes"
  })
}

resource "aws_instance" "reportes_instance_3" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_django.id,
    aws_security_group.trafico_ssh.id,
    aws_security_group.trafico_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-3"
    Role = "reportes"
  })
}

resource "aws_instance" "reportes_instance_4" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_django.id,
    aws_security_group.trafico_ssh.id,
    aws_security_group.trafico_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "reportes-instance-4"
    Role = "reportes"
  })
}

resource "aws_instance" "broker_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_broker
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_rabbit.id,
    aws_security_group.trafico_ssh.id
  ]

  tags = merge(local.common_tags, {
    Name = "broker-instance"
    Role = "rabbitmq"
  })
}

resource "aws_instance" "worker_email_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_ssh.id,
    aws_security_group.trafico_db.id
  ]

  tags = merge(local.common_tags, {
    Name = "worker-email-instance"
    Role = "worker-email"
  })
}

resource "aws_instance" "smtp_simulator_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_smtp
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [
    aws_security_group.trafico_smtp.id,
    aws_security_group.trafico_ssh.id
  ]

  tags = merge(local.common_tags, {
    Name = "smtp-simulator-instance"
    Role = "smtp-simulator"
  })
}

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
  vpc_security_group_ids = [aws_security_group.trafico_db.id]

  tags = merge(local.common_tags, {
    Name = "rds-postgresql"
    Role = "database"
  })
}

output "kong_public_ip" {
  value = aws_instance.kong_instance.public_ip
}

output "reportes_instance_1_public_ip" {
  value = aws_instance.reportes_instance_1.public_ip
}

output "reportes_instance_2_public_ip" {
  value = aws_instance.reportes_instance_2.public_ip
}

output "reportes_instance_3_public_ip" {
  value = aws_instance.reportes_instance_3.public_ip
}

output "reportes_instance_4_public_ip" {
  value = aws_instance.reportes_instance_4.public_ip
}

output "broker_instance_public_ip" {
  value = aws_instance.broker_instance.public_ip
}

output "worker_email_instance_public_ip" {
  value = aws_instance.worker_email_instance.public_ip
}

output "smtp_simulator_instance_public_ip" {
  value = aws_instance.smtp_simulator_instance.public_ip
}

output "rds_postgresql_endpoint" {
  value = aws_db_instance.rds_postgresql.address
}