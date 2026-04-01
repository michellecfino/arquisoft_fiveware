# Infraestructura para Experimentos
#
# Elementos a desplegar en AWS:
# 1. Grupos de seguridad:
#    - traffic-django (puerto 8080)
#    - traffic-db (puerto 5432)
#    - traffic-ssh (puerto 22)
#
# 2. Instancias EC2:
#    - db (PostgreSQL instalado y configurado)
#    - xxxx (app instalada y migraciones aplicadas)
#    - reportes (instancia del manejador de reportes)
# ******************************************************************

# ----------------------------
#         VARIABLES
# ----------------------------

variable "instance_count" {
  description = "Número de instancias EC2"
  default     = 4
}

variable "instance_type" {
  default = "t2.micro"
}

# ----------------------------
#         SEGURIDAD
# ----------------------------

# Define el grupo de seguridad para el tráfico de Django (8080)
resource "aws_security_group" "traffic_django" {
    name        = "${var.project_prefix}-traffic-django"
    description = "Allow application traffic on port 8080"

    ingress {
        description = "HTTP access for service layer"
        from_port   = 8080
        to_port     = 8080
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = merge(local.common_tags, {
        Name = "${var.project_prefix}-traffic-services"
    })
}

# Define el grupo de seguridad para la base de datos ()
resource "aws_security_group" "traffic_db" {
  name        = "${var.project_prefix}-traffic-db"
  description = "Allow PostgreSQL access"

  ingress {
    description = "Traffic from anywhere to DB"
    from_port   = 0000
    to_port     = 0000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-db"
  })
}

# Recurso. Define el grupo de seguridad para el tráfico SSH (22) y permite todo el tráfico saliente.
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


# ----------------------------
#         OUTPUTS
# ----------------------------

# Muestra la dirección IP pública de la instancia de la aplicación de XXXX.
output "XXXX_public_ip" {
  description = "Public IP address for xxxx service application"
  value       = aws_instance.XXXX.public_ip
}

# Muestra la dirección IP privada de la instancia de la aplicación de XXXX.
output "XXXX_private_ip" {
  description = "Private IP address for XXXX service application"
  value       = aws_instance.XXXX.private_ip
}

# Muestra la dirección IP privada de la instancia de la base de datos PostgreSQL.
output "database_private_ip" {
  description = "Private IP address for the PostgreSQL database instance"
  value       = aws_instance.database.private_ip
}

# ----------------------------
#         INSTANCIAS
# ----------------------------

# Define la instancia EC2 para el Manejador de Reportes
resource "aws_instance" "reportes" {
  count         = var.instance_count
  ami           = "ami-0c55b159cbfafe1f0" # Ubuntu
  instance_type = var.instance_type

  key_name = var.key_name

  vpc_security_group_ids = [aws_security_group.sg.id]

  user_data = file("user_data.sh")

  tags = {
    Name = "reportes-${count.index}"
  }
}

# Define la instancia EC2 para la base de datos PostgreSQL.
# Esta instancia incluye un script de creación para instalar y configurar PostgreSQL.
# El script crea un usuario y una base de datos, y ajusta la configuración para permitir conexiones remotas.
resource "aws_instance" "database" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_db.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash

              sudo apt-get update -y
              sudo apt-get install -y postgresql postgresql-contrib

              sudo -u postgres psql -c "CREATE USER fiveware WITH PASSWORD 'fiveware';"
              sudo -u postgres createdb -O monitoring_user monitoring_db
              echo "host all all 0.0.0.0/0 trust" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              echo "listen_addresses='*'" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              echo "max_connections=2000" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              sudo service postgresql restart
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-db"
    Role = "database"
  })
}

# Recurso. Define la instancia EC2 para la aplicación (Django).
# Esta instancia incluye un script de creación para instalar la aplicación y aplicar las migraciones


# ----------------------------
#       LOAD BALANCER
# ----------------------------
resource "aws_lb" "lb" {
  name               = "reportes-lb"
  load_balancer_type = "application"
  subnets            = ["subnet-xxxx", "subnet-yyyy"]
}

# ----------------------------
#          EXTRA
# ----------------------------

# Busca la AMI más reciente de Ubuntu 24.04 usando los filtros especificados.
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