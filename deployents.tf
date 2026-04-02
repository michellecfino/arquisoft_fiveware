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
#        BASE DE DATOS
# ----------------------------
resource "aws_security_group" "db_sg" {
  name        = "db-sg"
  description = "Permite acceso a PostgreSQL solo desde EC2"

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "costos-db"

  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = "costos"
  username = "admin"
  password = "Admin123!"

  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]

  publicly_accessible = false   # 
  multi_az            = false

  backup_retention_period = 0   # para experimento (más barato)

  skip_final_snapshot = true

  tags = {
    Name = "costos-db"
  }
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "db_port" {
  value = aws_db_instance.postgres.port
}

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

# 
resource "aws_security_group" "ec2_sg" {
  name = "ec2-sg"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

# ----------------------------
#         INSTANCIAS
# ----------------------------

# Define la instancia EC2 para el Manejador de Reportes
resource "aws_instance" "reportes" {
  count = var.instance_count

  ami           = "ami-ubuntu-24"
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  root_block_device {
    volume_size = 12
  }

  user_data = file("user_data.sh")

  tags = {
    Name = "reportes-${count.index}"
  }
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

# Recurso del API Gataway.
resource "aws_apigatewayv2_api" "api" {
  name          = "reportes-api"
  protocol_type = "HTTP"
}