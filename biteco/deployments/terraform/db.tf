variable "db_name" {
  description = "Nombre de la base de datos"
  type        = string
  default     = "biteco_latencia"
}

variable "db_username" {
  description = "Usuario maestro de PostgreSQL"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Password maestro de PostgreSQL"
  type        = string
  sensitive   = true
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# =========================================================
# Security Group - RDS PostgreSQL
# =========================================================

resource "aws_security_group" "traffic_rds" {
  name        = "${var.project_prefix}-traffic-rds"
  description = "Allow PostgreSQL access to Amazon RDS"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "PostgreSQL from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-rds"
  })
}

# =========================================================
# DB Subnet Group
# =========================================================

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${var.project_prefix}-rds-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-rds-subnet-group"
  })
}

# =========================================================
# Amazon RDS PostgreSQL
# =========================================================

resource "aws_db_instance" "database" {
  identifier             = "${var.project_prefix}-latencia-db"
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = "db.t3.micro"

  allocated_storage      = 20
  storage_type           = "gp3"
  storage_encrypted      = false

  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  port                   = 5432

  publicly_accessible    = true
  skip_final_snapshot    = true
  deletion_protection    = false
  multi_az               = false

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.traffic_rds.id]

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-latencia-db"
    Role = "database"
  })
}

output "database_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.database.address
}