resource "aws_db_instance" "postgres" {
  identifier        = "costos-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "costos"
  username          = "admin"
  password          = "Admin123!" 
  skip_final_snapshot = true
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}