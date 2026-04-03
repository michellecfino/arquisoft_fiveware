# Infraestructura para Experimento Escalabilidad
#
# Elementos a desplegar en AWS:
# 1. Grupos de seguridad:
#    - traffic-django (puerto 8000)
#    - traffic-db (puerto 5432)
#    - traffic-ssh (puerto 22)
#
# 2. Instancias EC2:
#    - db (PostgreSQL en RDS)
#    - reportes (cluster de 4 instancias)
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

  vpc_security_group_ids = [aws_security_group.db_sg.id]

  publicly_accessible     = false
  multi_az                = false
  backup_retention_period = 0
  skip_final_snapshot     = true

  tags = {
    Name = "costos-db"
  }
}

# ----------------------------
#   MANEJADOR DE REPORTES
# ----------------------------
variable "instance_count" {
  default = 4
}

resource "aws_instance" "reportes" {
  count = var.instance_count # 4 instancias

  ami           = "ami-ubuntu-24"
  instance_type = "t2.micro"

  vpc_security_group_ids = [aws_security_group.reportes_sg.id]

  root_block_device {
    volume_size = 12
  }

  user_data = file("user_data_reportes.sh")

  tags = {
    Name = "reportes-${count.index}"
  }
}

# SG para Reportes
resource "aws_security_group" "reportes_sg" {
  name = "reportes-sg"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group para Kong (API Gateway)
resource "aws_security_group" "kong_sg" {
  name = "kong-sg"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # JMeter
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

# ----------------------------
#       SERVIDOR KONG
# ----------------------------
resource "aws_instance" "kong" {
  ami           = "ami-ubuntu-24"
  instance_type = "t2.micro"

  vpc_security_group_ids = [aws_security_group.kong_sg.id]

  root_block_device {
    volume_size = 16
  }

  user_data = file("user_data_kong.sh")

  tags = {
    Name = "api-gateway-kong"
  }
}

# ----------------------------
#    OUTPUTS PARA JMETER
# ----------------------------
output "kong_public_ip" {
  value = aws_instance.kong.public_ip
}

output "reportes_private_ips" {
  value = aws_instance.reportes[*].private_ip
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "db_port" {
  value = aws_db_instance.postgres.port
}