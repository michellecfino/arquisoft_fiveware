# =========================================================
# Infraestructura experimento de latencia - BITECO
# =========================================================

# Variables
variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-2"
}

variable "project_prefix" {
  description = "Prefix used for naming AWS resources"
  type        = string
  default     = "biteco"
}

variable "instance_type" {
  description = "EC2 instance type for application hosts"
  type        = string
  default     = "t2.micro"
}

variable "db_instance_type" {
  description = "EC2 instance type for database host"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "AMI fija de Ubuntu para evitar DescribeImages"
  type        = string
  default     = "ami-0c803b171269e2d72"
}

# Provider
provider "aws" {
  region = var.region
}

# Locals
locals {
  repository = "https://github.com/michellecfino/arquisoft_fiveware.git"
  branch     = "latencia"
}

# =========================================================
# Security Groups
# =========================================================

resource "aws_security_group" "traffic_django" {
  name        = "${var.project_prefix}-traffic-django"
  description = "Allow application traffic on port 8080"

  ingress {
    description = "HTTP access for Django services"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-traffic-django"
  }
}

resource "aws_security_group" "traffic_kong" {
  name        = "${var.project_prefix}-traffic-kong"
  description = "Expose Kong proxy and admin ports"

  ingress {
    description = "Kong proxy"
    from_port   = 80
    to_port     = 80
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

  tags = {
    Name = "${var.project_prefix}-traffic-kong"
  }
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

  tags = {
    Name = "${var.project_prefix}-traffic-db"
  }
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

  tags = {
    Name = "${var.project_prefix}-traffic-ssh"
  }
}

# =========================================================
# EC2 - Kong
# =========================================================

resource "aws_instance" "kong" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_kong.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y docker.io git
              sudo systemctl enable docker
              sudo systemctl start docker

              cd /home/ubuntu
              if [ ! -d arquisoft_fiveware ]; then
                git clone ${local.repository}
              fi

              cd arquisoft_fiveware
              git fetch origin ${local.branch}
              git checkout ${local.branch}
              git pull origin ${local.branch}

              cd biteco_local
              sed -i 's|<ip-privada-manejador-reportes>|${aws_instance.manejador_reportes.private_ip}|g' kong/kong.yml

              sudo docker rm -f kong || true
              sudo docker run -d --name kong \
                -e KONG_DATABASE=off \
                -e KONG_DECLARATIVE_CONFIG=/usr/local/kong/declarative/kong.yml \
                -e KONG_PROXY_LISTEN=0.0.0.0:80 \
                -e KONG_ADMIN_LISTEN=0.0.0.0:8001 \
                -p 80:80 \
                -p 8001:8001 \
                -v /home/ubuntu/arquisoft_fiveware/biteco_local/kong/kong.yml:/usr/local/kong/declarative/kong.yml \
                kong:3.6
              EOT

  tags = {
    Name = "${var.project_prefix}-kong"
  }

  depends_on = [aws_instance.manejador_reportes]
}

# =========================================================
# EC2 - Database
# =========================================================

resource "aws_instance" "database" {
  ami                         = var.ami_id
  instance_type               = var.db_instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_db.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash

              sudo apt-get update -y
              sudo apt-get install -y postgresql postgresql-contrib git

              sudo -u postgres psql -c "CREATE USER admin_biteco WITH PASSWORD '123';" || true
              sudo -u postgres createdb -O admin_biteco biteco || true

              echo "host all all 0.0.0.0/0 trust" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              echo "listen_addresses='*'" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              echo "max_connections=2000" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              sudo systemctl restart postgresql

              cd /home/ubuntu
              if [ ! -d arquisoft_fiveware ]; then
                git clone ${local.repository}
              fi

              cd arquisoft_fiveware
              git fetch origin ${local.branch}
              git checkout ${local.branch}
              git pull origin ${local.branch}

              cd biteco_local
              PGPASSWORD=123 psql -h localhost -U admin_biteco -d biteco -f database/esquema_base.sql
              PGPASSWORD=123 psql -h localhost -U admin_biteco -d biteco -f database/seed_latencia.sql
              EOT

  tags = {
    Name = "${var.project_prefix}-db"
  }
}

# =========================================================
# EC2 - Agregador Costos
# =========================================================

resource "aws_instance" "agregador_costos" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_django.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y python3-pip git build-essential libpq-dev python3-dev

              cd /home/ubuntu
              if [ ! -d arquisoft_fiveware ]; then
                git clone ${local.repository}
              fi

              cd arquisoft_fiveware
              git fetch origin ${local.branch}
              git checkout ${local.branch}
              git pull origin ${local.branch}

              cd biteco_local
              sudo pip3 install --upgrade pip --break-system-packages
              sudo pip3 install -r requirements.txt --break-system-packages
              EOT

  tags = {
    Name = "${var.project_prefix}-agregador-costos"
  }

  depends_on = [aws_instance.database]
}

# =========================================================
# EC2 - Manejador Reportes
# =========================================================

resource "aws_instance" "manejador_reportes" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_django.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y python3-pip git build-essential libpq-dev python3-dev

              cd /home/ubuntu
              if [ ! -d arquisoft_fiveware ]; then
                git clone ${local.repository}
              fi

              cd arquisoft_fiveware
              git fetch origin ${local.branch}
              git checkout ${local.branch}
              git pull origin ${local.branch}

              cd biteco_local
              sudo pip3 install --upgrade pip --break-system-packages
              sudo pip3 install -r requirements.txt --break-system-packages
              EOT

  tags = {
    Name = "${var.project_prefix}-manejador-reportes"
  }

  depends_on = [aws_instance.database]
}

# =========================================================
# Outputs
# =========================================================

output "kong_public_ip" {
  description = "Public IP address for Kong"
  value       = aws_instance.kong.public_ip
}

output "agregador_costos_public_ip" {
  description = "Public IP address for agregador costos"
  value       = aws_instance.agregador_costos.public_ip
}

output "manejador_reportes_public_ip" {
  description = "Public IP address for manejador reportes"
  value       = aws_instance.manejador_reportes.public_ip
}

output "manejador_reportes_private_ip" {
  description = "Private IP address for manejador reportes"
  value       = aws_instance.manejador_reportes.private_ip
}

output "database_private_ip" {
  description = "Private IP address for PostgreSQL database instance"
  value       = aws_instance.database.private_ip
}

output "database_public_ip" {
  description = "Public IP address for PostgreSQL database instance"
  value       = aws_instance.database.public_ip
}