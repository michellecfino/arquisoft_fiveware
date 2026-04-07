provider "aws" {
  region = var.region
}

# ========================
# AMI UBUNTU
# ========================
data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ========================
# VPC DEFAULT
# ========================
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ========================
# SECURITY GROUP
# ========================
resource "aws_security_group" "general_sg" {
  name = "biteco-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8002
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

  ingress {
    from_port   = 5432
    to_port     = 5432
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

# ========================
# RDS
# ========================
resource "aws_db_instance" "postgres" {
  identifier         = "biteco-db"
  engine             = "postgres"
  engine_version     = "16"
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  db_name            = "bit_db"
  username           = "admin_user"
  password           = "michi1234"
  publicly_accessible = true
  skip_final_snapshot = true

  vpc_security_group_ids = [aws_security_group.general_sg.id]
}

# ========================
# RABBITMQ
# ========================
resource "aws_instance" "rabbitmq" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name = "biteco-key"

  vpc_security_group_ids = [aws_security_group.general_sg.id]

  user_data = file("../scripts/install_rabbit.sh")

  tags = {
    Name = "biteco-rabbitmq"
  }
}

# ========================
# LAUNCH TEMPLATE (APPS)
# ========================
resource "aws_launch_template" "app_template" {
  name_prefix   = "biteco-app-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name = "biteco-key"

  vpc_security_group_ids = [aws_security_group.general_sg.id]

  user_data = base64encode(templatefile("../scripts/install_app.sh", {
    rds_endpoint = aws_db_instance.postgres.address
    rabbitmq_ip  = aws_instance.rabbitmq.private_ip
  }))
}

# ========================
# TARGET GROUP
# ========================
resource "aws_lb_target_group" "app_tg" {
  name     = "biteco-tg"
  port     = 8001
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path = "/"
    port = "8001"
  }
}

# ========================
# ALB
# ========================
resource "aws_lb" "app_lb" {
  name               = "biteco-lb"
  load_balancer_type = "application"
  subnets            = data.aws_subnets.default.ids
}

# ========================
# LISTENER
# ========================
resource "aws_lb_listener" "listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = 8001
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

# ========================
# AUTOSCALING
# ========================
resource "aws_autoscaling_group" "asg" {
  desired_capacity = 2
  min_size         = 1
  max_size         = 5

  launch_template {
    id      = aws_launch_template.app_template.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.app_tg.arn]

  vpc_zone_identifier = data.aws_subnets.default.ids
}

# ========================
# KONG
# ========================
resource "aws_instance" "kong" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name = "biteco-key"

  vpc_security_group_ids = [aws_security_group.general_sg.id]

  user_data = templatefile("../scripts/install_kong.sh", {
    alb_dns = aws_lb.app_lb.dns_name
  })

  tags = {
    Name = "biteco-kong"
  }
}