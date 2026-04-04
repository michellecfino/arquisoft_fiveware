# ----------------------------
#      GRUPOS DE SEGURIDAD
# ----------------------------

# Regla de oro: El "Muro" que protege tus máquinas
resource "aws_security_group" "general_sg" {
  name        = "general-sg"
  description = "Permite SSH, HTTP y comunicacion interna"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Para que tú entres desde tu casa
  }

  ingress {
    from_port   = 8000
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Para Postman y JMeter
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Base de datos
  }

  ingress {
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # RabbitMQ
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ----------------------------
#        BASE DE DATOS (RDS)
# ----------------------------
resource "aws_db_instance" "postgres" {
  identifier        = "costos-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "costos"
  username          = "admin"
  password          = "Admin123!" # ¡No la cambies por ahora!
  vpc_security_group_ids = [aws_security_group.general_sg.id]
  publicly_accessible = true # Para que puedas verla desde tu PC
  skip_final_snapshot = true
}

# ----------------------------
#    BROKER (RABBITMQ) - EL NARAJA
# ----------------------------
resource "aws_instance" "broker" {
  ami           = "ami-0e2c8ccd4e0269736" # Ubuntu 24.04 LTS (Verifica tu region)
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.general_sg.id]
  tags = { Name = "Servidor-Broker-RabbitMQ" }
}

# ----------------------------
#    WORKERS - EL GRIS DEL MEDIO
# ----------------------------
resource "aws_instance" "workers" {
  ami           = "ami-0e2c8ccd4e0269736"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.general_sg.id]
  tags = { Name = "Servidor-Workers" }
}

# ----------------------------
#    CLUSTER DE REPORTES (LOS 4)
# ----------------------------
resource "aws_instance" "reportes" {
  count         = 4
  ami           = "ami-0e2c8ccd4e0269736"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.general_sg.id]
  tags = { Name = "reportes-${count.index}" }
}

# ----------------------------
#    GATEWAY (KONG)
# ----------------------------
resource "aws_instance" "kong" {
  ami           = "ami-0e2c8ccd4e0269736"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.general_sg.id]
  tags = { Name = "api-gateway-kong" }
}

# ----------------------------
#       RESULTADOS (IPs)
# ----------------------------
output "IP_GATEWAY_KONG" { value = aws_instance.kong.public_ip }
output "ENDPOINT_DB" { value = aws_db_instance.postgres.endpoint }
output "IP_BROKER" { value = aws_instance.broker.public_ip }