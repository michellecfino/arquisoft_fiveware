resource "aws_security_group" "apps_sg" {
  name        = "biteco_apps_sg"
  description = "Permitir trafico para Flask y Kong"

  ingress { from_port = 8000; to_port = 8001; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 22; to_port = 22; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 80; to_port = 80; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }

  egress { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"] }
}

# --- GATEWAY DEDICADO (KONG) ---
resource "aws_instance" "kong_gateway" {
  ami           = "ami-080e1f13689e07408"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.apps_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update
              sudo apt-get install -y docker.io
              sudo systemctl start docker
              sudo docker run -d --name kong \
                -e "KONG_DATABASE=off" \
                -e "KONG_ADMIN_LISTEN=0.0.0.0:8001" \
                -p 8000:8000 -p 8001:8001 \
                kong:latest
              EOF

  tags = { Name = "Biteco-Gateway-Kong" }
}

# --- PLANTILLA DE LAS APPS ---
resource "aws_launch_template" "flask_tpl" {
  name_id_prefix = "flask-app-tpl-"
  image_id      = "ami-080e1f13689e07408"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.apps_sg.id]

  user_data = base64encode(templatefile("../scripts/install_app.sh", {
    rds_endpoint = aws_db_instance.postgres_db.endpoint,
    rabbitmq_ip  = aws_instance.rabbitmq_server.public_ip
  }))

  tag_specifications {
    resource_type = "instance"
    tags = { Name = "Biteco-App-Node-ASG" }
  }
}

# --- GRUPO ELÁSTICO (ASG) ---
resource "aws_autoscaling_group" "flask_asg" {
  desired_capacity   = 2
  max_size           = 10
  min_size           = 1
  availability_zones = ["us-east-1a", "us-east-1b"]

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