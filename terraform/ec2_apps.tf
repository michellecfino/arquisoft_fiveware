resource "aws_security_group" "apps_sg" {
  name        = "biteco_apps_sg"
  description = "Permitir trafico para Flask y Kong"

  # Reglas de entrada (Ingress)
  ingress {
    from_port   = 8000
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

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Regla de salida (Egress)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- GATEWAY DEDICADO (KONG) ---
resource "aws_instance" "kong_gateway" {
  # ... (tus atributos previos) ...

  user_data = <<-EOF
              #!/bin/bash
              # 1. Límites del sistema
              echo "* soft nofile 65535" >> /etc/security/limits.conf
              echo "* hard nofile 65535" >> /etc/security/limits.conf
              sysctl -w fs.file-max=65535
              
              sudo apt-get update
              sudo apt-get install -y docker.io jq
              sudo systemctl start docker

              # 2. Lanzar Kong
              sudo docker run -d --name kong \
                -e "KONG_DATABASE=off" \
                -e "KONG_ADMIN_LISTEN=0.0.0.0:8001" \
                -e "KONG_PROXY_LISTEN=0.0.0.0:8000" \
                -e "KONG_NGINX_WORKER_CONNECTIONS=16384" \
                -p 8000:8000 -p 8001:8001 \
                kong:latest

              # Esperar a que Kong despierte
              sleep 10

              # 3. Configurar el CLUSTER (Upstream)
              # Creamos el Upstream
              curl -X POST http://localhost:8001/upstreams --data "name=flask_cluster"
              
              # Creamos el Servicio apuntando al Upstream
              curl -X POST http://localhost:8001/services \
                --data "name=biteco_service" \
                --data "host=flask_cluster"
              
              # Creamos la Ruta
              curl -X POST http://localhost:8001/services/biteco_service/routes \
                --data "paths[]=/"
              EOF
}

# --- PLANTILLA DE LAS APPS ---
resource "aws_launch_template" "flask_tpl" {
  # Cambiado a name_prefix que es el estándar
  name_prefix   = "flask-app-tpl-"
  image_id      = "ami-080e1f13689e07408"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.apps_sg.id]

  user_data = base64encode(templatefile("${path.module}/../scripts/install_app.sh", {
    rds_endpoint = aws_db_instance.postgres_db.endpoint,
    rabbitmq_ip  = aws_instance.rabbitmq_server.public_ip
    kong_private_ip = aws_instance.kong_gateway.private_ip 
  }))

  tag_specifications {
    resource_type = "instance"
    tags = { Name = "Biteco-App-Node-ASG" }
  }
}

# --- GRUPO ELÁSTICO (ASG) ---
resource "aws_autoscaling_group" "flask_asg" {
  desired_capacity   = 4
  max_size           = 10
  min_size           = 2
  availability_zones = ["us-east-1a", "us-east-1b"]
  health_check_grace_period = 300 
  health_check_type         = "EC2"

  launch_template {
    id      = aws_launch_template.flask_tpl.id
    version = "$Latest"
  }
}

# --- POLÍTICA DE CPU AL 50% ---
resource "aws_autoscaling_policy" "cpu_scaling" {
  name                   = "escalado-por-cpu"
  autoscaling_group_name = aws_autoscaling_group.flask_asg.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification { predefined_metric_type = "ASGAverageCPUUtilization" }
    target_value = 50.0
  }
}

output "IP_KONG" { value = aws_instance.kong_gateway.public_ip }
