resource "aws_db_instance" "database" {
  identifier             = "rds-postgresql-latencia"
  engine                 = "postgres"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  username               = "postgres"
  password               = "postgres123"
  db_name                = "biteco"
  skip_final_snapshot    = true
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.traffic_db.id]

  tags = merge(local.common_tags, {
    Name = "rds-postgresql-latencia",
    Role = "database"
  })
}

output "database_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.database.address
}