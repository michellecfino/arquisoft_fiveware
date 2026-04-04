variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "project_prefix" {
  description = "Prefijo del proyecto"
  type        = string
  default     = "biteco"
}

variable "repository" {
  description = "Repositorio git"
  type        = string
  default     = "https://github.com/michellecfino/arquisoft_fiveware.git"
}

provider "aws" {
  region = var.region
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

resource "aws_security_group" "traffic_ssh" {
  name        = "${var.project_prefix}-traffic-ssh"
  description = "SSH"

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

resource "aws_security_group" "traffic_django" {
  name        = "${var.project_prefix}-traffic-django"
  description = "Django 8080"

  ingress {
    from_port   = 8080
    to_port     = 8080
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

resource "aws_security_group" "traffic_db" {
  name        = "${var.project_prefix}-traffic-db"
  description = "PostgreSQL"

  ingress {
    from_port   = 5432
    to_port     = 5432
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

resource "aws_security_group" "traffic_kong" {
  name        = "${var.project_prefix}-traffic-kong"
  description = "Kong"

  ingress {
    from_port   = 80
    to_port     = 80
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

resource "aws_instance" "database" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_db.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              apt-get install -y postgresql postgresql-contrib git

              sudo -u postgres psql -c "CREATE USER admin_biteco WITH PASSWORD '123';"
              sudo -u postgres createdb -O admin_biteco biteco

              echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/16/main/pg_hba.conf
              echo "listen_addresses='*'" >> /etc/postgresql/16/main/postgresql.conf
              systemctl restart postgresql

              cd /home/ubuntu
              git clone ${var.repository}
              cd biteco_local

              PGPASSWORD=123 psql -h localhost -U admin_biteco -d biteco -f database/esquema_base.sql
              PGPASSWORD=123 psql -h localhost -U admin_biteco -d biteco -f database/seed_latencia.sql
              EOT

  tags = {
    Name = "${var.project_prefix}-db"
  }
}

resource "aws_instance" "agregador_costos" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.micro"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_django.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              apt-get install -y python3-pip git build-essential libpq-dev python3-dev

              cd /home/ubuntu
              git clone ${var.repository}
              cd biteco_local
              pip3 install -r requirements.txt --break-system-packages
              EOT

  tags = {
    Name = "${var.project_prefix}-agregador-costos"
  }

  depends_on = [aws_instance.database]
}

resource "aws_instance" "manejador_reportes" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.micro"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_django.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              apt-get install -y python3-pip git build-essential libpq-dev python3-dev

              cd /home/ubuntu
              git clone ${var.repository}
              cd biteco_local
              pip3 install -r requirements.txt --break-system-packages
              EOT

  tags = {
    Name = "${var.project_prefix}-manejador-reportes"
  }

  depends_on = [aws_instance.database]
}

resource "aws_instance" "kong" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.micro"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_kong.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io git

              systemctl enable docker
              systemctl start docker

              cd /home/ubuntu
              git clone ${var.repository}
              cd biteco_local

              sed -i "s|<ip-privada-manejador-reportes>|${aws_instance.manejador_reportes.private_ip}|g" kong/kong.yml

              docker run -d --name kong \
                -e KONG_DATABASE=off \
                -e KONG_DECLARATIVE_CONFIG=/usr/local/kong/declarative/kong.yml \
                -e KONG_PROXY_LISTEN=0.0.0.0:80 \
                -e KONG_ADMIN_LISTEN=0.0.0.0:8001 \
                -p 80:80 \
                -p 8001:8001 \
                -v /home/ubuntu/biteco_local/kong/kong.yml:/usr/local/kong/declarative/kong.yml \
                kong:3.6
              EOT

  tags = {
    Name = "${var.project_prefix}-kong"
  }

  depends_on = [aws_instance.manejador_reportes]
}

output "database_public_ip" {
  value = aws_instance.database.public_ip
}

output "database_private_ip" {
  value = aws_instance.database.private_ip
}

output "agregador_costos_public_ip" {
  value = aws_instance.agregador_costos.public_ip
}

output "manejador_reportes_public_ip" {
  value = aws_instance.manejador_reportes.public_ip
}

output "manejador_reportes_private_ip" {
  value = aws_instance.manejador_reportes.private_ip
}

output "kong_public_ip" {
  value = aws_instance.kong.public_ip
}