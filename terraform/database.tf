resource "aws_security_group" "rds_sg" {
  name        = "biteco_rds_sg"
  description = "Permitir trafico PostgreSQL"

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.apps_sg.id]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # En producción, usa tu IP específica
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres_db" {
  identifier           = "biteco-db-escalabilidad"
  engine               = "postgres"
  engine_version       = "15.4" # Versión estable y moderna
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  db_name              = "bit_db"
  username             = "admin_user"
  password             = "michi1234"
  publicly_accessible  = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  skip_final_snapshot  = true

  tags = {
    Name = "Biteco-Postgres-RDS"
  }
}

output "rds_endpoint" {
  value = aws_db_instance.postgres_db.endpoint
}