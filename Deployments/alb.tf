# LOAD BALANCER
resource "aws_lb" "lb" {
  name               = "reportes-lb"
  load_balancer_type = "application"
  subnets            = ["subnet-xxxx", "subnet-yyyy"]
}