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

resource "aws_security_group" "sg" {
  name = "reportes-sg"

  ingress {
    description = ""
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = ""
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = ""
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ----------------------------
#         OUTPUTS
# ----------------------------


# ----------------------------
#         INSTANCIAS
# ----------------------------
resource "aws_instance" "reportes" {
  count         = var.instance_count
  ami           = "ami-0c55b159cbfafe1f0" # Ubuntu
  instance_type = var.instance_type

  key_name = var.key_name

  vpc_security_group_ids = [aws_security_group.sg.id]

  user_data = file("user_data.sh")

  tags = {
    Name = "reportes-${count.index}"
  }
}

# ----------------------------
#       LOAD BALANCER
# ----------------------------
resource "aws_lb" "lb" {
  name               = "reportes-lb"
  load_balancer_type = "application"
  subnets            = ["subnet-xxxx", "subnet-yyyy"]
}