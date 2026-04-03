#importante para el trafico en las insrancias c:
resource "aws_security_group" "ec2_sg" {
  name        = "traffic-django-sg"
  description = "Permite trafico para que las apps lleguen a la DB"

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

# Balanceador de carga c:
resource "aws_lb" "app_lb" {
  name               = "fiveware-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ec2_sg.id]
  subnets            = ["", ""] #Esto hay que sacarlo de AWS
}

# listener, es como un broker
resource "aws_lb_listener" "front_end" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

#Grupo de destino
resource "aws_lb_target_group" "app_tg" {
  name     = "tg-reportes"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = "vpc-" # de nuevo, toca sabarlo de aws
}

# se crean las instancias 
resource "aws_instance" "nodos_app" {
  count         = 4 
  ami           = "" toca sacarlo de aws
  instance_type = "t3.micro" #opino que es mejor por desempeño y capacidad
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  tags = {
    Name = "Nodo-Escalabilidad-${count.index}"
  }
}

#conexión de las instancias con el balanceador
resource "aws_lb_target_group_attachment" "conectar_nodos" {
  count            = 4
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.nodos_app[count.index].id
  port             = 8080
}

# el listener y el balanceador de carga  para replicacion :D