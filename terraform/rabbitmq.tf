resource "aws_security_group" "rabbitmq_sg" {
  name        = "rabbitmq_sg"
  description = "Permitir trafico de mensajeria"

  ingress {
    description = "Puerto para envio de mensajes desde la App"
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  ingress {
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Puerto para la interfaz web (el que acabas de abrir)
  ingress {
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Puerto para entrar por terminal (el que nos dio error rojo)
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

resource "aws_instance" "rabbitmq_server" {
  ami           = "ami-080e1f13689e07408" # Ubuntu 24.04 LTS en us-east-1
  instance_type = "t3.micro"               # t3 tiene mejor manejo de ráfagas que t2

  vpc_security_group_ids = [aws_security_group.rabbitmq_sg.id]

  user_data = file("../scripts/install_rabbit.sh")

  tags = {
    Name = "Biteco-RabbitMQ-Broker"
  }
}

output "rabbitmq_public_ip" {
  value = aws_instance.rabbitmq_server.public_ip
}