# Security Group para la base de datos
resource "aws_security_group" "traffic_db" {
  name        = "biteco-traffic-db"
  description = "Allow PostgreSQL access"

  ingress {
    description = "Traffic to PostgreSQL"
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

  tags = {
    Name = "biteco-traffic-db"
  }
}