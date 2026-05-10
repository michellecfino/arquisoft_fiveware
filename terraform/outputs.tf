# =============================================================================
# outputs.tf
# Exposes key resource attributes after Terraform apply.
# These are used by CI/CD pipelines, scripts (fail_db.sh), and documentation.
# =============================================================================

# -------------------------------------------------------
# EC2 Instance Outputs
# -------------------------------------------------------

output "ec2_public_ips" {
  description = "Public IP addresses of the 4 application EC2 instances"
  value       = aws_instance.app_server[*].public_ip
}

output "ec2_private_ips" {
  description = "Private IP addresses of the 4 application EC2 instances"
  value       = aws_instance.app_server[*].private_ip
}

output "ec2_instance_ids" {
  description = "Instance IDs of the EC2 application servers"
  value       = aws_instance.app_server[*].id
}

output "ec2_public_dns" {
  description = "Public DNS names of the EC2 instances for SSH and HTTP access"
  value       = aws_instance.app_server[*].public_dns
}

# -------------------------------------------------------
# RDS Database Outputs
# -------------------------------------------------------

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (hostname:port) — use in Django settings.py DATABASE_HOST"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_db_name" {
  description = "PostgreSQL database name"
  value       = aws_db_instance.postgres.db_name
}

output "rds_instance_id" {
  description = "RDS instance identifier — used by fail_db.sh to target the correct instance"
  value       = aws_db_instance.postgres.id
}

# -------------------------------------------------------
# Security Group Outputs
# Required by fail_db.sh to revoke/restore RDS ingress rules
# to simulate network failure (Táctica: Heartbeat + Degradation)
# -------------------------------------------------------

output "rds_security_group_id" {
  description = "ID of the RDS security group — used by fail_db.sh to revoke ingress rules"
  value       = aws_security_group.rds_sg.id
}

output "ec2_security_group_id" {
  description = "ID of the EC2 security group — used by fail_db.sh as the source to revoke"
  value       = aws_security_group.ec2_sg.id
}



# -------------------------------------------------------
# Network Outputs
# -------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets (EC2)"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets (RDS)"
  value       = aws_subnet.private[*].id
}
