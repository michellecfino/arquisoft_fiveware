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