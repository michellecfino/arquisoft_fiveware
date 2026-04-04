resource "aws_security_group" "apps_sg" {
  name        = "biteco_apps_sg"
  description = "Permitir trafico para servicios Flask"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  ingress {
    from_port   = 8001
    to_port     = 8001
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

resource "aws_instance" "flask_nodes" {
  count         = 4
  ami           = "ami-080e1f13689e07408" # Ubuntu 24.04 LTS en us-east-1
  instance_type = "t2.micro"
  key_name      = "tu-llave-aws" # El nombre de tu archivo .pem en AWS

  vpc_security_group_ids = [aws_security_group.apps_sg.id]

  user_data = file("../scripts/install_app.sh")

  tags = {
    Name = "Biteco-App-Node-${count.index + 1}"
    Role = "API-Server"
  }
}

output "app_ips" {
  description = "IPs publicas de los nodos de aplicacion"
  value       = aws_instance.flask_nodes[*].public_ip
}